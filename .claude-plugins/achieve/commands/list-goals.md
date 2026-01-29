---
version: "1.0"
description: "List all goal sessions"
---

# /list-goals

List all goal sessions and their status.

## Instructions

1. Check if `.claude/achieve-sessions/index.yaml` exists

2. If the file does NOT exist:
   - Report: "No achieve sessions found."
   - Exit

3. If the file EXISTS:
   - Read the index file
   - Read each session's state.yaml for details
   - Display a table showing:
     - Session ID
     - Status (active, paused, achieved, max_iterations_reached)
     - Goal (truncated to 40 chars)
     - Current iteration / max iterations
     - Current phase

## Example Output

```
ACHIEVE SESSIONS

Active: abc123

ID      | Status  | Iter | Phase    | Goal
--------|---------|------|----------|----------------------------------
abc123* | active  | 5/30 | build    | Build a REST API with auth...
def456  | paused  | 2/50 | research | Improve strategy profitability...
ghi789  | achieved| 12/30| complete | Fix the login bug

* = currently active session
```

4. If there are no sessions, display:
```
No goal sessions found.

Start one with: /achieve:goal <goal description>
```
