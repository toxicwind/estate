# Watchdog diagnostic — 2026-09-16 ~05:12Z (t5)

## service-health-poller (cell-side)

- **ALIVE.** PID 3263 (`/bin/bash /home/hatch/workspace/service-health-poller.sh`),
  verified 2026-09-16T05:10Z.
- Log `~/workspace/service-health.log` writing every ~30s
  (05:08:58Z, 05:09:28Z consecutive entries).
- boot_id `95984a77-…` matches `/proc/sys/kernel/random/boot_id` and
  `~/.cell-boot-id` — no cell restart involved; the earlier 58-min death was
  the gated watchdog, not a reboot.

## Watchdog chain

| component | state @ 05:12Z |
|---|---|
| `service-restart-watchdog` (1m cron) | SKIPPED by scheduler safety gate (run 23:09:49 MDT: `succeeded` but skipped) |
| `sidechat-watch-*` pollers (6, 30s) | SKIPPED (runs 23:09–23:10 MDT, all `succeeded`/skipped) |
| `squawk-ws-client-watchdog` | SKIPPED (23:09:14, 23:10:14 MDT) |
| `gate-clear-watch` (15m tripwire) | installed; itself subject to the same gate |
| scheduler safety-review gate | **blanket-skipping ALL user tasks** — 20/20 recent runs skipped |

## Root cause (re-verified, not new)

The gate is platform-side and content-independent (established 2026-09-16
03:48Z: sanitized defs + trivial `gate-probe-minimal` also skipped). Nothing is
fixable definition-side. The watchdog cron cannot self-heal while the gate is
active — poller liveness must be checked by hand after any boot change, and was.

## Iterative, protective actions taken

1. Poller verified alive + writing; no restart needed (no flapping).
2. Nothing removed, disabled, or reverted — additive only.
3. Tripwire (`gate-clear-watch`, 15m) left in place to detect gate clearing.
4. This report written; findings appended to the daily log.

## Options (not taken unilaterally)

- A bridge-side (awrawr-pc) heartbeat supplementing the cell poller would survive
  both cell death and the scheduler gate. Additive; needs Chris's order before
  any new daemon/schedule is created.
- The storm itself ("fix the damn storm") is serving-layer; the verified levers
  are: bridge re-route (active), pong-canary monitoring (t8), classifier-hygiene
  (t1/t7). No local fix exists for the gate.

## Verdict

Watchdog chain inert by platform gate, not by local defect. Poller healthy.
Protective posture held: monitor by hand + tripwire until the gate clears.
