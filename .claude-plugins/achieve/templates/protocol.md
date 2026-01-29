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
- **FIRST: Discover relevant skills for this goal**
  - Run `ls .claude/skills/` to list available skills
  - Read each skill's SKILL.md description to understand what it does
  - Match skills to the goal (e.g., "strategy" in goal → strategy-writer skill)
  - Use matching skills/commands (e.g., `/strategy.write`) instead of manual implementation
- Run `/buildforce.build` to implement (using discovered skills where applicable)
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
