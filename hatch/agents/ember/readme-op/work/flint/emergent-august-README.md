# emergent-august

> **Unreliable-narrator environment hardening toolkit** — a snapshot of a live working session (2026-08-28/29) preserved as a GitHub repo: environment dotfiles, state-enforcer scripts, and parsed system logs from an agent runtime container.

![status: archived session snapshot](https://img.shields.io/badge/status-archived%20session%20snapshot-6c757d)
![session: 2026-08-28/29](https://img.shields.io/badge/session-2026--08--28%2F29-6c757d)

## Why it exists

This repo answers one question: *what did the August runtime environment actually look like, and which tools kept it healthy?* Everything here was captured live from a running agent container — the hardening scripts, the environment config, the state logs they produced.

## What's inside

| Path | Contents |
|------|----------|
| `auto_reapply.py` | Aggressively fast state enforcer (1-second check cycle) |
| `patch_apply.py` | Codex patch-format parser / applier |
| `git_helper.py` | Git clone fixer for overlayfs quirks |
| `bin/` | Tool shims (`t` command timer, `llm-shell` AI bash REPL, `gh`, `git`, `curl`) — some are legacy symlinks into `/mnt/agents/output` |
| `venv/bin/sgpt` | Shell-GPT in a Python venv |
| `sycophancy-lens/` | Standalone sub-project (own README): sycophancy detection lens with tests |
| `archives/session.zip` + `session_extracted/` | Original captured session bundle and extracted tree |
| `all_state_logs.json`, `state_log_*.json` | Parsed system state logs (kernel, CDP, ports, procs, VNC) |
| `audit_log.json` / `debug_network.json` | Security audit + Chrome DevTools network captures |
| `agents.md` | Agent operating notes from the session |
| `.env`, `.pip.conf`, `.gitconfig_fast` | Environment configuration captured live |

## Quick start

```bash
# Source the persistent environment
python3 auto_reapply.py --source > /tmp/env.sh
. /tmp/env.sh

# Run the state enforcer once (it was built for a 1-second check cycle)
python3 auto_reapply.py --once
```

## Environment provenance

The session ran on a Debian 12 (bookworm) container with dash as the shell:

- **Persistence** — drive9 FUSE mount at `/mnt/agents` (paths like `/mnt/agents/output/...` in the session refer to this; that mount is not part of this repo)
- **Init** — s6-svscan as PID 1
- **Browser** — Chromium with CDP on `:9222`
- **VNC** — KasmVNC on `:5901`/`:6080`
- **Runtime** — running as root with CAP_SYS_ADMIN

## ⚠️ Security note

This is an un-sanitized session capture. `.env` contains a GitHub PAT from August 2026 — **rotate it, treat it as expired** — and some scripts assume root. Read before running.

---

*Session: emergent-august-28th · captured 2026-08-28/29 · archived as-is*
