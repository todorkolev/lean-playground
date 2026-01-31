#!/bin/bash

# Achieve Plugin Stop Hook
# Multi-session aware loop management
# Based on ralph-wiggum's stop hook

set -euo pipefail

# Read hook input from stdin
HOOK_INPUT=$(cat)

# Session management paths
SESSIONS_DIR=".claude/achieve-sessions"
INDEX_FILE="$SESSIONS_DIR/index.yaml"

# Get transcript path from hook input (needed for session detection)
TRANSCRIPT_PATH=$(echo "$HOOK_INPUT" | jq -r '.transcript_path')

if [[ ! -f "$TRANSCRIPT_PATH" ]]; then
  # No transcript - allow exit
  exit 0
fi

# Determine active session from transcript markers (transparent parallel support)
# Look for ACHIEVE_SESSION markers in the transcript
# FIX: Use -E for extended regex and + (one or more) instead of * (zero or more)
# This prevents matching empty session IDs like "ACHIEVE_SESSION: "
ACTIVE_SESSION=$(grep -oE 'ACHIEVE_SESSION: [a-f0-9]+' "$TRANSCRIPT_PATH" 2>/dev/null | tail -1 | sed 's/ACHIEVE_SESSION: //' || echo "")

# No fallback to index.yaml - if no ACHIEVE_SESSION marker in transcript,
# this is not an achieve:goal conversation and we should not interfere

if [[ -z "$ACTIVE_SESSION" ]] || [[ "$ACTIVE_SESSION" == "null" ]]; then
  # No active session - allow exit
  exit 0
fi

# Session state file
SESSION_DIR="$SESSIONS_DIR/$ACTIVE_SESSION"
LOOP_STATE_FILE="$SESSION_DIR/loop.md"

if [[ ! -f "$LOOP_STATE_FILE" ]]; then
  # Session exists but no loop state - allow exit
  exit 0
fi

# Check if session is already completed (don't interfere with completed sessions)
SESSION_STATUS=$(grep '^status:' "$SESSION_DIR/state.yaml" 2>/dev/null | sed 's/status: *//' || echo "active")
case "$SESSION_STATUS" in
  complete|achieved|cancelled|max_iterations_reached|failed)
    # Session is done - clear from index if needed and allow exit
    if [[ -f "$INDEX_FILE" ]]; then
      sed -i 's/^active_session:.*/active_session: null/' "$INDEX_FILE" 2>/dev/null || true
    fi
    exit 0
    ;;
esac

# Parse loop state (markdown with YAML frontmatter)
FRONTMATTER=$(sed -n '/^---$/,/^---$/{ /^---$/d; p; }' "$LOOP_STATE_FILE")
ITERATION=$(echo "$FRONTMATTER" | grep '^iteration:' | sed 's/iteration: *//')
MAX_ITERATIONS=$(echo "$FRONTMATTER" | grep '^max_iterations:' | sed 's/max_iterations: *//')
COMPLETION_PROMISE=$(echo "$FRONTMATTER" | grep '^completion_promise:' | sed 's/completion_promise: *//' | sed 's/^"\(.*\)"$/\1/')

# Validate numeric fields
if [[ ! "$ITERATION" =~ ^[0-9]+$ ]]; then
  echo "Warning: Achieve session $ACTIVE_SESSION has corrupted iteration count" >&2
  exit 0
fi

if [[ ! "$MAX_ITERATIONS" =~ ^[0-9]+$ ]]; then
  echo "Warning: Achieve session $ACTIVE_SESSION has corrupted max_iterations" >&2
  exit 0
fi

# Check if max iterations reached
if [[ $MAX_ITERATIONS -gt 0 ]] && [[ $ITERATION -ge $MAX_ITERATIONS ]]; then
  echo "Achieve session $ACTIVE_SESSION: Max iterations ($MAX_ITERATIONS) reached."
  # Mark session as completed in index
  sed -i "s/status: active/status: max_iterations_reached/" "$SESSION_DIR/state.yaml" 2>/dev/null || true
  # Remove from active
  sed -i "s/^active_session:.*/active_session: null/" "$INDEX_FILE"
  exit 0
fi

# Transcript already validated above

# Read last assistant message from transcript
if ! grep -q '"role":"assistant"' "$TRANSCRIPT_PATH"; then
  echo "Warning: No assistant messages in transcript" >&2
  exit 0
fi

LAST_LINE=$(grep '"role":"assistant"' "$TRANSCRIPT_PATH" | tail -1)
if [[ -z "$LAST_LINE" ]]; then
  exit 0
fi

LAST_OUTPUT=$(echo "$LAST_LINE" | jq -r '
  .message.content |
  map(select(.type == "text")) |
  map(.text) |
  join("\n")
' 2>&1)

if [[ $? -ne 0 ]] || [[ -z "$LAST_OUTPUT" ]]; then
  exit 0
fi

# Check for completion promise (ONLY exact match ends session)
if [[ "$COMPLETION_PROMISE" != "null" ]] && [[ -n "$COMPLETION_PROMISE" ]]; then
  PROMISE_TEXT=$(echo "$LAST_OUTPUT" | perl -0777 -pe 's/.*?<promise>(.*?)<\/promise>.*/$1/s; s/^\s+|\s+$//g; s/\s+/ /g' 2>/dev/null || echo "")

  # ONLY exact match ends the session - partial achievements continue iterating
  if [[ -n "$PROMISE_TEXT" ]] && [[ "$PROMISE_TEXT" = "$COMPLETION_PROMISE" ]]; then
    echo "Achieve session $ACTIVE_SESSION: Goal achieved! <promise>$COMPLETION_PROMISE</promise>"
    # Mark session as completed
    sed -i "s/status: active/status: achieved/" "$SESSION_DIR/state.yaml" 2>/dev/null || true
    sed -i "s/^active_session:.*/active_session: null/" "$INDEX_FILE"
    exit 0
  fi
fi

# Not complete - continue loop with same prompt
NEXT_ITERATION=$((ITERATION + 1))

# Extract prompt from loop state file
PROMPT_TEXT=$(awk '/^---$/{i++; next} i>=2' "$LOOP_STATE_FILE")

if [[ -z "$PROMPT_TEXT" ]]; then
  echo "Warning: No prompt text in loop state" >&2
  exit 0
fi

# Update iteration counter
TEMP_FILE="${LOOP_STATE_FILE}.tmp.$$"
sed "s/^iteration: .*/iteration: $NEXT_ITERATION/" "$LOOP_STATE_FILE" > "$TEMP_FILE"
mv "$TEMP_FILE" "$LOOP_STATE_FILE"

# Build system message
GOAL_SUMMARY=$(grep '^goal:' "$SESSION_DIR/state.yaml" 2>/dev/null | head -1 | sed 's/goal: *//' | cut -c1-40 || echo "unknown")
if [[ "$COMPLETION_PROMISE" != "null" ]] && [[ -n "$COMPLETION_PROMISE" ]]; then
  SYSTEM_MSG="Achieve [$ACTIVE_SESSION] iteration $NEXT_ITERATION | Goal: $GOAL_SUMMARY... | To complete: <promise>$COMPLETION_PROMISE</promise>"
else
  SYSTEM_MSG="Achieve [$ACTIVE_SESSION] iteration $NEXT_ITERATION | Goal: $GOAL_SUMMARY..."
fi

# Output JSON to block stop and feed prompt back
jq -n \
  --arg prompt "$PROMPT_TEXT" \
  --arg msg "$SYSTEM_MSG" \
  '{
    "decision": "block",
    "reason": $prompt,
    "systemMessage": $msg
  }'

exit 0
