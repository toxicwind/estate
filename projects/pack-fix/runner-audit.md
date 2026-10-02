# Hatch runner audit — 2026-09-20 (runner-watch, pack-fix lane)

Evidence window: cell scheduler definitions + run histories observed
2026-09-20 21:18–21:45 UTC (15:18–15:45 MDT). Swarm was auto-paused by the
crash-prevention interlock during the tail of the audit (hatch load1 > 10).

## Verdicts applied

| runner | verdict | cost before | action |
|---|---|---|---|
| `kimi-auto-canary-judge` (5m) | **fake-completed** — five consecutive successes, all "phase=0 idle … HOLD — no active canary"; yote `cron-judge.sh` exits 0 on phase 0 by design; the canary's own runlog says the cron was "created DISABLED — enabled at Phase 1" | 288 agent runs/day | **DISABLED** (cron.update, 15:33 MDT) with re-enable trigger in the body; the def was subsequently fully removed from the scheduler (archived def at `cron.d/_archive/kimi-auto-canary-judge__interval@5m.md` retains the Phase-1 re-enable note). Final state: not scheduled, 0 runs/day |
| `audit-bridge-watch` (5m, disabled) | **orphan** — disabled, 2 consecutive scheduler failures (last 03:03 MDT); the Nemotron-vs-Kimi audit it watched is already complete (results JSON + live verdict in memory) | 0 runs/day, stale def | **REMOVED** (cron.remove 15:33 MDT; def archived to `cron.d/_archive/`). **Resurrection caught 15:50–15:53 MDT:** goal-sync re-created the def and re-enabled it (one run fired at 15:50:36). Re-disabled via cron.update; corrected the stale `GOAL.md` (it still described the audit as blocked and the watcher as by-design — the likely resurrection trigger). Final state: `enabled:false`, no queued runs. If it resurrects again, the goal-sync mechanism needs runner-auditor's def-hygiene lane. Note: goal file `goals/live-nemotron-vs-kimi-herd-audit/GOAL.md` now records completion |
| `progress-watchdog` (3m → **5m**) | real runner, cadence too hot — its script sends a 30-min pulse and dedupes alerts for 1800s, so 3m dispatch (480 runs/day) is pure overhead | 480 runs/day | **CADENCE → 5m** (288/day, next run 15:37 MDT). Body rewrite is Suture/hesitance-hunt's lane (mid-rewrite, untouched). Failure-escalation for run-level failures (e.g. 15:04 MDT service-restart-mid-exec no-output run) proposed in fleet; fold in after the body rewrite lands |

## Not fake (evidence-based, left alone)

- `bridge-watchdog` (5m) — five recent silent successes; authenticated bridge/WS health.
- `yote-connector-watch` (5m) — five recent successes incl. a manual recovery-trigger run; local `:18301` listener.
- `squawk-monitor` (5m) — recent successes; one failure at 13:58 MDT was a known-outage skip misclassified as `account_action_required` (classification noise, not fakery).
- `swarm-watchdog` (5m) — real intervention at 15:04 MDT (auto-paused hatch at load1 12.1).
- `heartbeat` (30m), `agentic-feature-tour` (daily), system feed pulses — out of scope / runtime-managed.

## Overlap map (not duplicates)

`bridge-watchdog` (remote bridge/WS) vs `yote-connector-watch` (local :18301)
vs `squawk-monitor` (fleet message consumer) vs yote `squawk-watchdog.timer`
(backend liveness) vs `swarm-watchdog` (load interlock) vs `progress-watchdog`
(market/bidder/daemon supervision) — distinct scopes, complementary.

## Spindle

No process, systemd unit, timer, cron job, pitchfork daemon, or durable memory
entry named "spindle" exists. The word appears only as a scope placeholder in
fleet messages and one todo line. Conclusion: **not an installed
runner/component — an undefined scope word**, not something to audit.

## Permanent inventory

`bin/runner-inventory.sh` — re-run anytime on the hatch cell; flags disabled,
orphan-owned, duplicate-id, missing-script, canary-idle, and trashed defs.
