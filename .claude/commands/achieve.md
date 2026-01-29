---
version: "1.0"
description: "Achieve a goal using iterative development with Buildforce phases"
---

# /achieve Command

Goal: $ARGUMENTS

---

## STEP 1: Parse the Goal

Analyze the goal text above and extract:

### Success Criteria

Look for these patterns in the goal:
- "tests pass", "all tests" → Run test suite, expect 0 failures
- "builds", "compiles" → Build/compile succeeds
- "> X", "< Y", ">= Z" → Numeric thresholds (e.g., "Sharpe > 0.5", "latency < 100ms")
- "works", "functional", "working" → Feature operates without errors
- "returns X", "outputs Y" → Specific output expected
- "without errors", "no crashes" → Error-free execution
- "complete", "implemented", "added" → Feature exists and is functional

Extract ALL success criteria found. If multiple criteria exist, ALL must be met.

### Complexity Estimate

Based on the scope of the goal:
- **Simple** (10 iterations): Single file changes, bug fixes, small additions
- **Medium** (30 iterations): Multi-file changes, new features, refactoring
- **Complex** (50 iterations): Architectural changes, new systems, major features

---

## STEP 2: Decide Whether to Ask Questions

**ONLY ask if success criteria are truly unclear.**

Examples where you should NOT ask (criteria are clear):
- "Add endpoint that returns JSON" → Success = endpoint exists, returns JSON
- "Fix the login bug" → Success = login works without the bug
- "Make tests pass" → Success = all tests pass
- "Build a feature with X" → Success = feature X works

Examples where you SHOULD ask:
- "Improve the homepage" → What improvement? Performance? Design? Content?
- "Make it better" → Better how? What metric?
- "Optimize the app" → What target? Speed? Memory? Size?

If criteria ARE clear from the goal text:
→ Skip to STEP 3

If criteria are NOT clear:
→ Use AskUserQuestion tool with a single focused question:
  - Question: "What would indicate this goal is achieved?"
  - Provide 2-4 concrete options based on the goal context
  - Example options: "All tests pass", "Performance < 100ms", "Feature X works"

---

## STEP 3: Confirm and Initialize

Display this summary:

```
ACHIEVE: [Goal summary - first 60 chars]

Success Criteria:
- [Criterion 1]
- [Criterion 2]
- ...

Complexity: [Simple/Medium/Complex] ([10/30/50] iterations max)

Initializing...
```

Create the state file `.claude/.achieve-state.yaml`:

```yaml
goal: "[Full goal text]"
success_criteria:
  - "[Criterion 1]"
  - "[Criterion 2]"
max_iterations: [10/30/50]
started_at: "[ISO timestamp]"
current_phase: "research"
attempts: []
```

---

## STEP 4: Start the Achieve Loop

Now start the ralph-wiggum loop with this prompt:

```
/ralph-wiggum:ralph-loop "You are working toward a goal. Read .claude/.achieve-state.yaml for the goal and criteria. Follow the ACHIEVE LOOP PROTOCOL below.

ACHIEVE LOOP PROTOCOL:

1. READ STATE
   - Check .claude/.achieve-state.yaml for goal, criteria, phase
   - Check .buildforce/buildforce.json for session state
   - Check .buildforce/sessions/*/plan.yaml for progress

2. ROUTE BY PHASE

   A. phase=research (no buildforce session):
      → Run /buildforce.research with the goal
      → Update phase to 'plan' in state file

   B. phase=plan (research done, no plan):
      → Run /buildforce.plan to create implementation plan
      → Update phase to 'build' in state file

   C. phase=build (plan exists):
      → Run /buildforce.build to implement
      → After build completes, update phase to 'validate'

   D. phase=validate (build complete):
      → Test against each success criterion
      → If ALL criteria pass:
         - Run /buildforce.complete
         - Output: <promise>ACHIEVED</promise>
      → If ANY criterion fails:
         - Log attempt in state file
         - Update phase back to 'build'
         - Analyze failure and plan fix

3. LOG ATTEMPTS
   After each validation, add to attempts in state file:
   ```yaml
   attempts:
     - iteration: N
       result: pass/fail
       details: what worked/failed
   ```

4. COMPLETION
   When ALL success criteria are met:
   - Summarize what was accomplished
   - Output: <promise>ACHIEVED</promise>
" --max-iterations [10/30/50] --completion-promise "ACHIEVED"
```

Replace `[10/30/50]` with the complexity-based iteration count.

---

## IMPORTANT RULES

1. **Do not over-engineer**: Implement exactly what's needed to meet the criteria
2. **Validate frequently**: Check criteria after each significant change
3. **Log failures**: Track what was tried to avoid repeating mistakes
4. **Simplify on failure**: If something isn't working after several attempts, try a simpler approach
5. **Be honest**: If a criterion can't be validated automatically, note it

---

## FAILURE HANDLING

If max iterations reached without success:

```
GOAL NOT FULLY ACHIEVED ([N] iterations)

Goal: [goal]

Progress:
- [What was accomplished]

Remaining:
- [What criteria still not met]

Suggestion: [What to try next]

<promise>ACHIEVED - PARTIAL</promise>
```
