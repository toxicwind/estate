---
name: tau-tmux
description: Run parallel tau experiments in tmux and audit the live tau install — launcher chain, dist binary version, PI_CONFIG_DIR, skills discovery, and router reachability. Real checks, real exit codes.
---

# tau-tmux — tmux lab + live tau audit

Two jobs: (1) a tmux lab for running multiple tau experiments in parallel,
(2) a real audit of the tau install on this box. Every check below verifies
something that exists. Nothing here audits files that were deleted.

## tmux lab recipes

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
bun run /home/toxic/sovereign/skills/tau-tmux/helper/audit.ts [--verbose]
```

Checks (each prints PASS/FAIL; exit 0 = all pass, 1 = any fail):

1. `tau` on PATH is the launcher script and its collapse chain resolves
   (TAU_BIN → PATH → ./tau → dist/omp → bun src).
2. `tau --version` reports the expected engine (18.2.6+).
3. `PI_CONFIG_DIR=.tau` is honored: `$HOME/.tau/agent/config.yml` exists.
4. Skills: `~/.tau/agent/skills` symlink exists, target is a directory, and
   at least one `SKILL.md` is discoverable under it.
5. Routers reachable: herd `http://127.0.0.1:25100/v1/models` and sovereign
   `http://127.0.0.1:25104/v1/models` answer within the timeout.
6. No stale config: `nvidia.json` / `cascade.json` do not exist under
   `/home/toxic/sovereign` (removed 2026-09-20; provider catalog is
   `~/.tau/agent/models.yml`).

## What this skill is NOT

It does not audit NVIDIA unlock files — those were removed when the provider
catalog moved to `models.yml` with herd/sovereign dynamic discovery. If you
need provider ranking evidence, see the `paper-search` skill and the ranker
reports, not this skill.
