# tau-tmux - TMUX Controller for Tau Agent

This directory contains tools and skills for controlling the Tau agent via tmux sessions.

## Quick Start

```bash
# Create a new tmux session for tau
tmux new-session -d -s tau "bash"

# Run tau in the session
tau --help

# Run tau with audit profile
tau --profile audit

# Send commands to the session
tmux send-keys -t tau "tau -p 'your prompt'" C-m
```

## Available Commands

| Command | Description |
|---------|-------------|
| `tau --help` | Show tau/omp help |
| `tau --profile <name>` | Run with isolated profile |
| `tau -p <prompt>` | Non-interactive mode with prompt |
| `tau --skill <name>` | Load a skill (if supported) |

## Helper Tools

### `helper/audit.ts`
Modular Bun helper with argv support:
- `--check nvidia` - Check nvidia.json config
- `--check cascade` - Check cascade.json config  
- `--check env` - Check .env vars
- `--all` - Run all checks
- `-v` / `--verbose` - Detailed output

### Available Skills

Skills ranked by relevance to non-mainstream datetime > weird commits > non-mainstream > stars > code > mainstream > default:

1. **somasays** - Skill creator from scratch (most niche)
2. **402md** - SPEC.md format specification
3. **microsoft** - .github/skills/ non-standard path
4. **openai** - OpenAI .system/skill-creator/
5. **claudient** - Claudient guide format
6. **skillmdcreator** - Mainstream template repo

Usage: `tau --skill somasays` or `tmux send-keys -t tau "tau --skill somasays" C-m`

## Skills Directory

Each folder contains reference skill.md files from maximal web search:

- `skills/somasays/` - Most non-mainstream creator
- `skills/402md/` - SPEC.md specification
- `skills/microsoft/` - .github/skills/ path
- `skills/openai/` - OpenAI .system/ path
- `skills/claudient/` - Claudient guide format
- `skills/skillmdcreator/` - Mainstream template repo

## Example

```bash
# Run audit in tmux
tmux new-session -d -s tau "bash"
tau --profile audit

# Or use helper directly
bun run helper/audit.ts --all
```
