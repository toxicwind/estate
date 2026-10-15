# tau-tmux — tmux lab, agent swarms & live tau audit

Powered by [`corral`](https://github.com/toxicwind/ranch/tree/main/barn/corral) — the universal Estate Ranch terminal multiplexer and agent swarm orchestrator (`~/.local/bin/corral`).

Jobs:
1. Multi-agent swarms and parallel tau experiments via `corral swarm` and `corral lab`.
2. Developer solo sessions with multi-socket discovery (`corral solo`).
3. Live `o200k_harmony` token counting and output telemetry (`corral tok`).
4. Real production audit of the live tau install on this host (`helper/audit.ts`).

## corral & tmux lab recipes

```bash
# Start an isolated developer session
corral solo dev

# Start a 3-pane experiment lab
corral lab tau-lab 3

# Launch a 4-agent swarm grid
corral swarm agent-grid 4

# Send command to pane 0 (non-focus-stealing)
corral send agent-grid:0 "tau -p 'reply PANE0_READY'"

# Measure output token usage live (crashless o200k_harmony)
corral tok agent-grid:0

# Capture output non-destructively
corral capture agent-grid:0

# Clean shutdown
corral kill agent-grid
```

### Raw tmux lab recipes

```bash
# New detached lab session with 3 panes
tmux new-session -d -s tau-lab -n lab
tmux split-window -h -t tau-lab
tmux split-window -v -t tau-lab:0.1
tmux attach -t tau-lab

# Run a tau probe in a pane without stealing focus
tmux send-keys -t tau-lab:0.0 "tau -p 'reply with exactly: PANE0_OK'" C-m

# Read a pane's output programmatically
tmux capture-pane -t tau-lab:0.0 -p | tail -20

# Wait for a pane's command to finish (event-driven, no sleep loop)
tmux wait-for -S done &  # in the pane: <cmd>; tmux wait-for -S done
```

Parallel experiment pattern: one pane per variable (different `--skills`
filter, different `--profile`, different model role). Compare
`capture-pane` outputs. Keep what works, kill the session when done
(`tmux kill-session -t tau-lab`).

## Skill flags that actually exist

- `--skills "<glob>"` — filter discovered skills, e.g. `--skills "paper-*"`.
  There is NO `--skill <name>` flag; the singular form does not exist.
- `--profile <name>` — isolated profile; only `default` exists unless you
  create more under `~/.tau/profiles/`.
- `-p/--print` — non-interactive, process prompt and exit.
- `--no-skills` — disable skills discovery entirely (fastest boot).

## Audit (helper/audit.ts)

```bash
bun run /home/toxic/estate/skills/tau-tmux/helper/audit.ts [--verbose]
```

Checks (each prints PASS/FAIL; exit 0 = all pass, 1 = any fail):

1. `tau` on PATH is the launcher script and its collapse chain resolves
   (TAU_BIN → PATH → ./tau → tau → bun src).
2. `tau --version` reports the expected engine (18.2.6+).
3. `PI_CONFIG_DIR=.tau` is honored: `$HOME/.tau/agent/config.yml` exists.
4. Skills: `~/.tau/agent/skills` symlink exists, target is a directory, and
   at least one `SKILL.md` is discoverable under it.
5. Routers reachable: herd `http://127.0.0.1:25100/v1/models` and estate
   `http://127.0.0.1:25104/v1/models` answer within the timeout.
6. No stale config: `nvidia.json` / `cascade.json` do not exist under
   `/home/toxic/estate` (removed 2026-09-20; provider catalog is
   `~/.tau/agent/models.yml`).

## What this skill is NOT

It does not audit NVIDIA unlock files — those were removed when the provider
catalog moved to `models.yml` with herd/estate dynamic discovery. If you
need provider ranking evidence, see the `paper-search` skill and the ranker
reports, not this skill.