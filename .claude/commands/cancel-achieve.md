---
version: "1.0"
description: "Cancel an active achieve loop"
---

# /cancel-achieve

Cancel the currently active achieve loop.

## Instructions

1. Check if `.claude/.achieve-state.yaml` exists

2. If the file EXISTS:
   - Read the goal from the file
   - Delete the file `.claude/.achieve-state.yaml`
   - Also run `/ralph-wiggum:cancel-ralph` to stop the ralph loop
   - Report: "Cancelled: [goal summary]"

3. If the file does NOT exist:
   - Report: "No active achieve loop to cancel."

## Example Output

If active loop exists:
```
Cancelled achieve loop.

Goal was: Build a REST API with authentication
Progress: 5 iterations completed
Phase: build

State file removed. Ralph loop cancelled.
```

If no active loop:
```
No active achieve loop to cancel.
```
