# Achieve Plugin

Goal-driven iterative development with multi-session support.

## Commands

| Command | Description |
|---------|-------------|
| `/achieve:goal <goal>` | Start a new goal session |
| `/achieve:list-goals` | List all sessions and their status |
| `/achieve:cancel-goal [id]` | Cancel a session (active if no id) |

## How It Works

1. **Parse goal**: Extract success criteria from goal text
2. **Create session**: Generate unique ID, create state files
3. **Loop**: Stop hook intercepts exit, continues until done
4. **Complete**: Output `<promise>ACHIEVED</promise>` when criteria met

## Session Management

Sessions are stored in `.claude/achieve-sessions/`:

```
.claude/achieve-sessions/
├── index.yaml              # Active session + list
├── abc123/
│   ├── state.yaml          # Goal, criteria, attempts
│   ├── loop.md             # Ralph-style loop state
│   └── protocol.md         # Loop instructions
└── def456/
    └── ...
```

## Multi-Session Support

- Start multiple sessions (each gets unique ID)
- Only one session active at a time per terminal
- Previous session paused when new one starts

## Parallel Sessions (Multiple Terminals)

Run multiple goals in parallel using separate terminal sessions:

```bash
# Terminal 1
claude
/achieve:goal "Build REST API"

# Terminal 2
claude
/achieve:goal "Fix auth bug"
```

Each terminal runs its own independent loop. Session tracking happens transparently via transcript markers - no environment variables needed.

## Integration with Buildforce

Uses buildforce phases for structured development:
- Research → Plan → Build → Validate → Complete

## Stop Criteria

The loop stops when:
1. You output `<promise>ACHIEVED</promise>` (goal complete)
2. Max iterations reached (default: 50)
