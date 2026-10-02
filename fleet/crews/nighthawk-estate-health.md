---
crew: 'nighthawk-estate-health'
scope: 'estate-health watch: tonight listener/daemon/cron health sweep (yote round-trip, :25100/:25104/:25109/:25101/:25147/:25135/:25110 probes, pitchfork daemon list, cell crons incl. overnight-watch morning brief); fix what is obviously broken'
owner: 'Nighthawk (Ember's crew)'
status: 'RUNNING (2026-09-30)'
order: 63
registered: '2026-09-30'
updated: '2026-09-30'
---

# nighthawk-estate-health

Per-crew ownership record. Edit the frontmatter above; the §2 table in
`docs/fleet-knowledgebase.md` is generated from these files — do not edit it by hand.
After changing this file, run `bun projects/ops/bin/kb-rollup.ts`.

## Sweep 2026-09-30 ~12:40-13:00 GMT

- yote-conn exec round-trip: OK (awrawr-pc, 16-core box, load ~3.06).
- Listeners verified with REAL responses, not just port-open:
  - :25100 herd — `/health` → OK; :25104 sovereign-router v3.2 — `/health` JSON ok, 112 live models
  - :25109 keypool — `/health` ok (7 pools, all keys healthy)
  - :25101 model-guard — OK; :25110 grafana — HTTP 200
  - :25135 squawk-feed — `/squawk-feed/ping` → `{"seq": 1790772066180}` (seq advancing; note: feed routes live under `/squawk-feed/*`, `/seq` 404s — not a fault)
  - :25147 squawk-ws — socket open, returns HTTP 401 to a bad WS handshake (live HTTP server; full WS auth check out of lane scope)
- pitchfork: all daemons running except three stopped:
  - FIXED: sovereign/redis (valkey :25199) — stopped since 03:32 GMT after SIGTERM despite `auto=["start"]` + `retry=true`. Restarted via `pitchfork start sovereign/redis`; verified LISTEN + PING → PONG. Config in pitchfork.toml untouched (was already correct).
  - sovereign/bidder-forge + sovereign/bidder-scout — processes HEALTHY and running ~6.5h on the correct new paths (projects/range/ranch/oracle/bin/bidder.py via launcher .sh); pitchfork state.toml desync shows "stopped" while processes run (the .sh idempotency guard documents this exact desync; duplicates exit 0). Historical crash (00:34 GMT) was the old path /agents/oracle-market/bin/ + missing `cryptography` module — superseded: current launchers use /usr/bin/python3 which has cryptography 50.0.1. No action taken beyond observation (supervisor state desync is cosmetic; editing state.toml live is riskier than the bug).
- Crons (cell): all present and enabled — bridge-watchdog, squawk-monitor, swarm-watchdog, swarm-throttle, progress-watchdog, agent-reaper, fleet-outbox-flush, worker-queue-dispatch/watch-keepalive, heartbeat. `overnight-watch-morning-brief` enabled, runonce fires 2026-09-30 09:11 MDT (15:11 GMT), 0 consecutive failures. Intentionally disabled (not my call to touch): audit-bridge-watch (audit lane finished), yote-connector-watch (connector setup DONE).
- Gap: fleet-onboard.sh --register fails from the hatch cell (it reads KB from /home/toxic/... locally and GitHub raw fallback fails through the proxy; cell /tmp is 100% full 512M tmpfs so KB can't be staged locally). Registration done by writing this crew file directly on yote instead.
