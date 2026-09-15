# Fleet Audit — 2026-09-14 18:04 MDT

Auditor: subagent 5a33059d (fleet audit lane, parent 67fcb771)

## Fleet Summary

**Running roots (6):**
- `f99a2d06` — main-chat root (running)
- `67fcb771` — coordinator root, main channel (this audit's parent)
- `58246538` — root (running)
- `7240686c` — HFT-latency coordinator root (running, ~48h old)
- `cfc15812`, `ef1092e9` — roots (just spawned, running)

**Running subagents (10):**
- Under `67fcb771` (5): fleet-audit (5a33059d, me), monorepo-audit (3bfbee82),
  hft-bench-audit (cef01df5), build-server-research (0c2e1e16), c2-skill (17b00cee)
- Under `7240686c` (5): HFT coordinator (3d071f2a) + 4 workers
  (81199adb, 253f01e8, 0cf35d2b, 0f16dd2c)

**Errored (terminal, 14):** All from ~14h ago (03:50 incident). Already dead, nothing to stop.

## Squawk State (awrawr-pc)

- **Repo:** /home/toxic/squawk/ — chat repo present (agent_chat, fleet_*.py, chat.py, etc.)
- **squawk-root:** fleet/ (0001, 0002, 10000, 10001, 10002 + log.jsonl),
  keys/ (agent1, breaker, relay, shingle, yote — all present), leads/
- **squawk-ws:** NOW pitchfork-owned (PID 2248059, started 18:04, sovereign/squawk-ws running)
- **squawk-feed:** STILL MANUAL (PID 2097378, nohup since 16:23, port 25135).
  pitchfork.toml HAS [daemons.squawk-feed] but it can't start — port squatted.
- **Directives:** latest broadcast 17:38 MDT — /home/toxic/AGENTS.md created (bridge standing rules).

## STOP LIST (for coordinator decision)

1. **PID 2097378** — manual `squawk_feed.py` (port 25135). Blocks pitchfork sovereign/squawk-feed.
   Started 16:23 via nohup run-feed.sh. Safe to kill; pitchfork will start the defined daemon.

2. **PID 2167511** — manual `awrawr_ws_exec.py` (port 8379). Causes pitchfork
   sovereign/awrawr-ws-exec to error (EADDRINUSE). Started 17:04. Safe to kill;
   pitchfork will start the defined daemon. NOTE: do NOT restart awrawr-mcp.service
   from inside a bridge call (kills the caller).

3. **PID 2095376** — orphaned `inotifywait` from the OLD manual squawk-ws (16:21).
   The new pitchfork squawk-ws (2248059) spawned its own inotifywait (2248063).
   Safe to kill; it's watching the same dirs redundantly.

## REDUNDANCY FLAG

- **HFT overlap:** New `cef01df5` (HFT LATENCY + BENCH AUDIT, under 67fcb771, spawned 18:04)
  vs existing HFT coordinator `3d071f2a` + 4 workers (under 7240686c, active —
  last msg: "All four HFT work streams are now running in parallel").
  The new bench audit should COORDINATE with the existing HFT lane, not duplicate it.
  Recommend: have cef01df5 read the HFT coordinator's state before starting bench work.

## Pitchfork Status

- `sovereign/squawk-ws` — running (pitchfork-owned since 18:04)
- `sovereign/squawk-feed` — NOT running (blocked by manual PID 2097378)
- `sovereign/awrawr-ws-exec` — errored (blocked by manual PID 2167511)
- `sovereign/buildsrv` — running (new)
- Others (coyote, herd, kimi-auto-resolver, nim-proxy, shep, etc.) — running
