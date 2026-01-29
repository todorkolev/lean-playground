---
version: "1.0"
description: "Achieve a goal using iterative development with Buildforce phases"
argument-hint: "<goal description>"
allowed-tools: ["Bash(${CLAUDE_PLUGIN_ROOT}/scripts/setup-session.sh:*)"]
---

# /goal Command

Goal: $ARGUMENTS

---

## STEP 1: Parse the Goal

Analyze the goal text above and extract:

### Success Criteria

Look for these patterns in the goal:
- "tests pass", "all tests" → Run test suite, expect 0 failures
- "builds", "compiles" → Build/compile succeeds
- "> X", "< Y", ">= Z" → Numeric thresholds (e.g., "Sharpe > 0.5")
- "works", "functional" → Feature operates without errors
- "returns X", "outputs Y" → Specific output expected
- "profitable", "profitability" → Positive returns, good metrics
- "minimum risk", "low risk" → Low drawdown, low volatility

Extract ALL success criteria found. Format as YAML list items.

### Complexity Estimate

- **Simple** (10 iterations): Single file changes, bug fixes
- **Medium** (30 iterations): Multi-file changes, new features
- **Complex** (50 iterations): Architectural changes, major features

---

## STEP 2: Clarify If Needed

**ONLY ask if success criteria are truly unclear.**

Examples where you should NOT ask:
- "Build API with tests passing" → Success = tests pass
- "Fix the login bug" → Success = login works
- "Improve strategy profitability" → Success = better metrics

Examples where you SHOULD ask:
- "Improve the homepage" → What improvement?
- "Make it better" → Better how?

If criteria are clear → Skip to STEP 3
If criteria are unclear → Ask using AskUserQuestion

---

## STEP 3: Create Session

Display summary:

```
ACHIEVE: [Goal summary - first 50 chars]

Success Criteria:
- [Criterion 1]
- [Criterion 2]

Complexity: [Simple/Medium/Complex] ([10/30/50] iterations)

Creating session...
```

Run the setup script:

```!
"${CLAUDE_PLUGIN_ROOT}/scripts/setup-session.sh" "$ARGUMENTS" --max-iterations [N] --success-criteria "- criterion 1
- criterion 2"
```

Replace `[N]` with 10, 30, or 50 based on complexity.

After the script completes, it outputs a session ID. You MUST immediately output this marker:

```
ACHIEVE_SESSION: <session_id>
```

This marker enables parallel sessions in different terminal windows.

---

## STEP 4: Begin Working

After the session is created, immediately begin working on the goal.

Read the protocol file and state file that were created, then start with Phase 1 (research) of the buildforce workflow.

The stop hook will automatically continue the loop when you try to exit until either:
1. You output `<promise>ACHIEVED</promise>` (only when truly complete)
2. Max iterations reached

---

## IMPORTANT RULES

1. **Do not over-engineer**: Implement exactly what's needed
2. **Validate frequently**: Check criteria after each change
3. **Log failures**: Track attempts to avoid repeating mistakes
4. **Be honest**: Only output the promise when criteria are truly met
