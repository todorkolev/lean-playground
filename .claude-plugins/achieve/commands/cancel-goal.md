---
version: "1.0"
description: "Cancel a goal session"
argument-hint: "[session-id | --all]"
---

# /cancel-goal

Cancel a goal session.

## Usage

- `/cancel-goal` - Cancel the currently active session
- `/cancel-goal <id>` - Cancel a specific session by ID
- `/cancel-goal --all` - Cancel all sessions

## Instructions

### If `--all` is specified:

1. Delete the entire `.claude/achieve-sessions/` directory
2. Report: "All achieve sessions cancelled."

### If a session ID is specified:

1. Check if `.claude/achieve-sessions/<id>/` exists
2. If not: Report "Session <id> not found."
3. If yes:
   - Delete the session directory
   - Remove the session from index.yaml
   - If this was the active session, set active_session to null
   - Report: "Session <id> cancelled: <goal summary>"

### If no argument (cancel active):

1. Read `.claude/achieve-sessions/index.yaml`
2. Get the active_session value
3. If null or empty: Report "No active session to cancel."
4. If active:
   - Delete the session directory
   - Remove from index.yaml
   - Set active_session to null
   - Report: "Active session <id> cancelled: <goal summary>"

## Example Output

```
Session abc123 cancelled.

Goal was: Build a REST API with authentication
Progress: 5 iterations completed
Phase: build

Session removed.
```

Or if no active session:

```
No active goal session to cancel.

To cancel a specific session: /achieve:cancel-goal <session-id>
To see all sessions: /achieve:list-goals
```
