---
name: evolve.learn
description: Capture a learning, insight, or pattern into a skill's knowledge folder. Use when you discover something worth remembering for future sessions.
allowed-tools: Read, Write, Glob
argument-hint: "[learning description] [--skill SKILL] [--file FILE]"
---

# Capture Learning

Capture a learning from the current conversation into the appropriate skill's knowledge folder.

## Arguments

- `$ARGUMENTS`: The learning description and optional flags
  - `--skill SKILL`: Target skill (default: infer from context)
  - `--file FILE`: Target knowledge file (default: infer from topic)

## Workflow

### Step 1: Parse Input

Extract from `$ARGUMENTS`:
- The learning description (everything before flags)
- Target skill (if `--skill` provided, else infer)
- Target file (if `--file` provided, else infer)

### Step 2: Infer Target (if not specified)

If skill not specified:
- Look at recent conversation context
- If discussing strategies/backtesting → `strategy-writer`
- If discussing learning/reflection → `evolve`
- If unclear → ask user

If file not specified:
- Analyze the learning content
- Match keywords to existing knowledge files
- If no match → create new file or ask user

### Step 3: Load Knowledge File

Read the target knowledge file:
- `.claude/skills/{skill}/knowledge/{file}.yaml`

If file doesn't exist:
- Create it with proper header structure
- Update `_index.yaml`

### Step 4: Generate Entry

Create a new entry following the schema:

```yaml
- id: "{PREFIX}-{NNN}"  # e.g., ES-004 for entry-signals
  created: "{TODAY}"
  type: pattern | anti-pattern | insight  # infer from content
  confidence: 0.5  # always start at 0.5
  validations: 0

  summary: "{ONE_LINE_SUMMARY}"
  context: "{WHEN_THIS_APPLIES}"
  details: |
    {DETAILED_EXPLANATION}

  tags: [{RELEVANT_KEYWORDS}]
```

### Step 5: Write Entry

Append the new entry to the knowledge file's `entries` array.

### Step 6: Confirm

Output:
```
Learning captured:
- Skill: {skill}
- File: {file}
- ID: {entry_id}
- Summary: {summary}
```

## Examples

```
/evolve.learn "RSI divergence works better with volume confirmation" --skill strategy-writer --file entry-signals
```

```
/evolve.learn "Always check if position exists before adding to it"
```

```
/evolve.learn "Capturing the 'why' makes learnings more valuable" --skill evolve
```

## ID Prefixes by File

Use these prefixes for entry IDs:
- `entry-signals.yaml` → ES-NNN
- `exit-rules.yaml` → EX-NNN
- `risk-management.yaml` → RM-NNN
- `mistakes.yaml` → MK-NNN
- `capture-patterns.yaml` → CP-NNN
- `reflection-patterns.yaml` → RP-NNN
- Other files → First two letters of filename
