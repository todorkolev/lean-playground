#!/bin/bash

# Achieve Session Setup Script
# Creates a new achieve session with unique ID

set -euo pipefail

# Parse arguments
GOAL=""
MAX_ITERATIONS=50
COMPLETION_PROMISE="ACHIEVED"
SUCCESS_CRITERIA=""

print_help() {
  cat << 'HELP_EOF'
Achieve Session Setup

USAGE:
  setup-session.sh "<goal>" [OPTIONS]

ARGUMENTS:
  goal                              Goal description

OPTIONS:
  --max-iterations <n>              Max iterations (default: 50)
  --completion-promise <text>       Promise text (default: ACHIEVED)
  --success-criteria <yaml>         YAML list of success criteria
  -h, --help                        Show this help

EXAMPLES:
  setup-session.sh "Build a REST API" --max-iterations 30
  setup-session.sh "Fix auth bug" --success-criteria "- tests pass"
HELP_EOF
  exit 0
}

while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)
      print_help
      ;;
    --max-iterations)
      MAX_ITERATIONS="$2"
      shift 2
      ;;
    --completion-promise)
      COMPLETION_PROMISE="$2"
      shift 2
      ;;
    --success-criteria)
      SUCCESS_CRITERIA="$2"
      shift 2
      ;;
    *)
      if [[ -z "$GOAL" ]]; then
        GOAL="$1"
      fi
      shift
      ;;
  esac
done

if [[ -z "$GOAL" ]]; then
  echo "Error: No goal provided" >&2
  echo "Usage: setup-session.sh \"<goal>\" [OPTIONS]" >&2
  exit 1
fi

# Generate unique session ID (6 char hex)
SESSION_ID=$(head -c 3 /dev/urandom | xxd -p)

# Paths
SESSIONS_DIR=".claude/achieve-sessions"
INDEX_FILE="$SESSIONS_DIR/index.yaml"
SESSION_DIR="$SESSIONS_DIR/$SESSION_ID"

# Create directories
mkdir -p "$SESSION_DIR"

# Create/update index file
if [[ ! -f "$INDEX_FILE" ]]; then
  cat > "$INDEX_FILE" << EOF
# Achieve Sessions Index
active_session: "$SESSION_ID"
sessions:
  - id: "$SESSION_ID"
    created_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    status: active
EOF
else
  # Check if index file is valid (has active_session line)
  if ! grep -q '^active_session:' "$INDEX_FILE" 2>/dev/null; then
    # Index file is malformed, recreate it
    cat > "$INDEX_FILE" << EOF
# Achieve Sessions Index
active_session: "$SESSION_ID"
sessions:
  - id: "$SESSION_ID"
    created_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    status: active
EOF
  else
    # Pause current active session if any
    CURRENT_ACTIVE=$(grep '^active_session:' "$INDEX_FILE" | sed 's/active_session: *//' | tr -d '"')
    if [[ -n "$CURRENT_ACTIVE" ]] && [[ "$CURRENT_ACTIVE" != "null" ]]; then
      # Mark previous as paused
      if [[ -f "$SESSIONS_DIR/$CURRENT_ACTIVE/state.yaml" ]]; then
        sed -i "s/status: active/status: paused/" "$SESSIONS_DIR/$CURRENT_ACTIVE/state.yaml" 2>/dev/null || true
      fi
    fi

    # Update active session
    sed -i "s/^active_session:.*/active_session: \"$SESSION_ID\"/" "$INDEX_FILE"

    # Add new session to list
    cat >> "$INDEX_FILE" << EOF
  - id: "$SESSION_ID"
    created_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    status: active
EOF
  fi
fi

# Create session state file
cat > "$SESSION_DIR/state.yaml" << EOF
goal: "$GOAL"
session_id: "$SESSION_ID"
status: active
max_iterations: $MAX_ITERATIONS
started_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
current_phase: "research"
success_criteria:
$SUCCESS_CRITERIA
attempts: []
EOF

# Create loop state file (ralph-style frontmatter + prompt)
cat > "$SESSION_DIR/loop.md" << EOF
---
active: true
iteration: 1
max_iterations: $MAX_ITERATIONS
completion_promise: "$COMPLETION_PROMISE"
started_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
---

Read and follow .claude/achieve-sessions/$SESSION_ID/protocol.md exactly.
Goal state is in .claude/achieve-sessions/$SESSION_ID/state.yaml.
EOF

# Create protocol file
cat > "$SESSION_DIR/protocol.md" << 'PROTOCOL_EOF'
# Achieve Loop Protocol

Read the goal and success criteria from the state.yaml file in this session directory.

## Each Iteration

### 1. READ STATE
- Check `state.yaml` in this session directory for goal, criteria, phase
- Check `.buildforce/buildforce.json` for buildforce session state
- Check `.buildforce/sessions/*/plan.yaml` for progress

### 2. ROUTE BY PHASE

**A. phase=research** (no buildforce session):
- Run `/buildforce.research` with the goal
- Update phase to 'plan' in state.yaml

**B. phase=plan** (research done, no plan):
- Run `/buildforce.plan` to create implementation plan
- Update phase to 'build' in state.yaml

**C. phase=build** (plan exists):
- Run `/buildforce.build` to implement
- After build completes, update phase to 'validate'

**D. phase=validate** (build complete):
- Test against each success criterion from state.yaml
- If ALL criteria pass:
  - Run `/buildforce.complete`
  - Output: `<promise>ACHIEVED</promise>`
- If ANY criterion fails:
  - Log attempt in state.yaml under `attempts:`
  - Update phase back to 'build'
  - Analyze failure and plan fix

### 3. LOG ATTEMPTS
After each validation, add to attempts in state.yaml:
```yaml
attempts:
  - iteration: N
    result: pass/fail
    details: what worked/failed
```

### 4. COMPLETION
When ALL success criteria are met:
- Summarize what was accomplished
- Output: `<promise>ACHIEVED</promise>`

### 5. MAX ITERATIONS
If max iterations reached without full success:
- Summarize progress made
- List remaining criteria not met
- Output: `<promise>ACHIEVED - PARTIAL</promise>`
PROTOCOL_EOF

# Output success message
cat << EOF
Achieve session created!

Session ID: $SESSION_ID
Goal: ${GOAL:0:60}$([ ${#GOAL} -gt 60 ] && echo "...")
Max iterations: $MAX_ITERATIONS
Completion promise: $COMPLETION_PROMISE

Session files:
  State: $SESSION_DIR/state.yaml
  Loop:  $SESSION_DIR/loop.md
  Protocol: $SESSION_DIR/protocol.md

The stop hook is now active for this session.
EOF

echo ""
echo "$SESSION_ID"
