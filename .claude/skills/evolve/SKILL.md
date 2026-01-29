---
name: evolve
description: Self-improvement engine that captures learnings and updates skill knowledge. Use when you want to record an insight, pattern, or mistake for future reference.
allowed-tools: Read, Write, Glob, Grep
---

# Evolve Skill

The evolve skill manages learning capture and reflection for all skills in this project, including itself.

## Purpose

- Capture learnings from conversations and experiences
- Store knowledge in skill-specific `knowledge/` folders
- Update confidence scores based on evidence
- Enable skills to improve through use

## Knowledge Location

Each skill has its own knowledge folder:
- `~/.claude/skills/{skill-name}/knowledge/`

This skill's own knowledge lives at:
- `~/.claude/skills/evolve/knowledge/`

## Commands

This skill provides two commands:
- `/evolve.learn` - Capture a single learning
- `/evolve.reflect` - Session retrospective to extract multiple learnings

## Knowledge Schema

All knowledge files follow the schema defined in:
- Read `knowledge/_index.yaml` for the list of knowledge files
- Each file contains `entries` with: id, type, confidence, summary, context, details, evidence, tags

## Workflow

When capturing a learning:
1. Identify the target skill (default: infer from conversation context)
2. Identify the knowledge file (default: infer from learning topic)
3. Generate a unique entry ID
4. Create entry with confidence 0.5
5. Update the knowledge file
6. Update `_index.yaml` if new file created

When reflecting:
1. Review conversation for insights, mistakes, patterns
2. For each finding, run the capture workflow
3. Log the reflection in `evolve/knowledge/reflection-patterns.yaml`
