---
name: evolve
description: |
  AUTO-INVOKE to capture learnings after productive work sessions.
  Silently records patterns, anti-patterns, and insights to any skill's knowledge folder.
  Triggers on: error resolution, successful implementations, discovered patterns, or explicit reflection.
allowed-tools: Read, Write, Glob, Grep
---

# Evolve - Self-Improvement Engine

**Universal skill that captures learnings to improve any skill's knowledge base.**

Operate silently unless explicitly asked to reflect.

## When to Auto-Invoke

Capture learnings when you observe:
- Bug fixes or error resolutions
- Successful implementations worth remembering
- Patterns that worked or failed
- Anti-patterns to avoid
- Insights about tools, APIs, or approaches

## Silent Capture Workflow

1. **Identify target skill** from conversation context
   - Look at what domain the work was in
   - Check which skills have knowledge folders in `.claude/skills/*/knowledge/`

2. **Identify knowledge file** within that skill
   - Match the learning topic to existing files
   - Create new file if needed (update `_index.yaml`)

3. **Generate entry**:
   ```yaml
   - id: "{PREFIX}-{NNN}"
     created: "{TODAY}"
     type: pattern | anti-pattern | insight
     confidence: 0.5
     validations: 0
     summary: "{ONE_LINE}"
     context: "{WHEN_APPLIES}"
     details: |
       {EXPLANATION}
     tags: [{KEYWORDS}]
   ```

4. **Append** to knowledge file

5. **Update** `_index.yaml` entry count

## ID Prefixes

Use first two letters of filename + sequential number:
- `capture-patterns.yaml` → CP-NNN
- `reflection-patterns.yaml` → RP-NNN
- `{custom-file}.yaml` → {XX}-NNN

## Explicit Reflection

When user asks to reflect:
1. Scan conversation for all learnings
2. Capture each to appropriate skill/file
3. Update existing entries if validated/contradicted:
   - Validation: `confidence += 0.1` (max 1.0)
   - Contradiction: `confidence -= 0.15` (min 0.0)
4. Summarize what was captured

## Knowledge Locations

Each skill maintains its own knowledge:
- `.claude/skills/{skill-name}/knowledge/`

This skill's meta-knowledge about learning capture:
- `.claude/skills/evolve/knowledge/`
