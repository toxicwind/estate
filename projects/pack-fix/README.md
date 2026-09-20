# pack-fix

Pack-fix lane: hatch-side task-runner + watchdog **behavior** fixes, hesitance
fixes, orphaned processes, durable todos, and fleet personas/culture.

Part of [sovereign-projects](../../README.md) — see the [projects index](../README.md).

## What lives here

- [`bin/runner-inventory.sh`](bin/runner-inventory.sh) — permanent hatch-side
  runner inventory. Reads the cell's cron.d definitions (user, goal-owned,
  system, archive) and emits a markdown table with cadence, runs/day, and
  heuristic flags (`disabled`, `orphan-owner`, `duplicate-id`,
  `missing-script`, `canary-idle`, `system-readonly`, `trashed`).
  Run it on the hatch cell: `HATCH_WS=~/workspace ./bin/runner-inventory.sh`.
- [`runner-audit.md`](runner-audit.md) — the 2026-09-20 audit verdicts:
  per-runner purpose, last real finding vs fake-ok, cost, and decision.

## Lane boundaries (Chris directive, 2026-09-20)

- **Mine:** behavior fixes for hatch-side runners (canary-judge phase-aware
  disable, progress-watchdog cadence + failure-escalation, disabled
  audit-bridge-watch orphan removal), this inventory script.
- **runner-auditor:** cron-def hygiene (trash stale defs), yote systemd units,
  swarm state. No dupes — sync in fleet before re-probing.
- **hesitance-hunt / Suture:** progress-watchdog body rewrites — coordinate,
  never overwrite.
- **Out:** /tmp migration → kimi-unlock-audit; orphan→repo → repo-integrator-max.

## Standing rules

- No monkeypatching: fixes live in real files, committed, restart-surviving.
- The script is the deliverable; running it once is proof.
- Commit to canonical `toxicwind/sovereign-projects` main only, fetch-first,
  no force-push, verify the remote SHA.
