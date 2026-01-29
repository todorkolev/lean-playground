---
name: evolve.reflect
description: Session retrospective that analyzes the conversation to extract learnings. Use at the end of a productive session or after backtest results.
allowed-tools: Read, Write, Glob, Grep
---

# Session Reflection

Analyze the current session to extract and capture multiple learnings.

## Workflow

### Step 1: Gather Context

Collect information about the session:
1. Review conversation for:
   - Strategies written or modified
   - Backtests run and their results
   - Errors encountered and how they were fixed
   - Decisions made and their rationale
   - Surprises (things that didn't work as expected)

2. If recent backtest results exist:
   - Read results from `results/` directory
   - Extract key metrics: Sharpe, drawdown, win rate, etc.

### Step 2: Identify Learnings

For each category, look for learnings:

**Successes (patterns)**
- What worked well?
- What approach led to good results?
- What should be repeated?

**Failures (anti-patterns)**
- What didn't work?
- What caused poor results?
- What should be avoided?

**Insights**
- What was surprising?
- What assumption was proven wrong?
- What new understanding emerged?

### Step 3: Classify Each Learning

For each identified learning, determine:
- **Skill**: Which skill does this apply to?
- **File**: Which knowledge file is most relevant?
- **Type**: pattern | anti-pattern | insight
- **Confidence**: Start at 0.5, increase if strong evidence

### Step 4: Capture Learnings

For each learning, invoke the capture workflow:
1. Generate entry following schema
2. Append to appropriate knowledge file
3. Track what was captured

### Step 5: Update Existing Entries

If a learning validates or contradicts an existing entry:
- Find the existing entry
- Update its `validations` or `contradictions` count
- Adjust `confidence` accordingly:
  - Validation: confidence = min(1.0, confidence + 0.1)
  - Contradiction: confidence = max(0.0, confidence - 0.15)

### Step 6: Log Reflection

Add an entry to `evolve/knowledge/reflection-patterns.yaml` if any meta-insights about the reflection process itself emerged.

### Step 7: Summary

Output a summary:

```
Session Reflection Complete

Learnings captured:
- [skill/file] ID: summary
- [skill/file] ID: summary

Existing entries updated:
- [ID] confidence: 0.5 → 0.6 (validated)
- [ID] confidence: 0.7 → 0.55 (contradicted)

Skills affected: strategy-writer, evolve
```

## Triggers

This command is especially useful after:
- Running a backtest (`lp backtest ...`)
- Completing a strategy implementation
- Fixing a bug or error
- A session with multiple iterations

## Example Output

```
Session Reflection Complete

Learnings captured:
- [strategy-writer/entry-signals] ES-005: Volume confirmation improves RSI signals
- [strategy-writer/mistakes] MK-003: Don't use market orders in low liquidity

Existing entries updated:
- [ES-001] confidence: 0.5 → 0.6 (validated by crypto_momentum backtest)

Skills affected: strategy-writer
Total new entries: 2
Total updates: 1
```
