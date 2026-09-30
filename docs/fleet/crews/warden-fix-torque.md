---
crew: 'warden-fix-torque'
scope: 'Fix ferrous-warden self-alert loop: bless herd rebuild, self-watch exclusion, breaker dedupe key'
owner: 'Torque (Ember crew)'
status: 'DONE (2026-09-30)'
order: 54
registered: '2026-09-30'
updated: '2026-09-30'
---

# warden-fix-torque

Torque the wolverine — warden lane, fixing the ferrous-warden self-alert loop
(Chris 2026-09-30: "Fix warden pleass lol").

Root cause: Stampede's 00:08 herd rebuild was never recorded in declared
intent (deploy/manifest.yaml), so every inotify event tripped drift; 6
restores in 6 minutes opened the circuit breaker; per-event inotify kinds
(CREATE/MODIFY/DELETE) embedded in alert bodies defeated the (title,body)
dedupe, giving x4 fleet posts in 8s. A 00:20:55 bin/ checkout also fired the
loop on the warden's own binary.

What happened mid-fix: the lane fell back to the FALLBACK-blessed binary
(e1d70dd0) — the warden itself restored it at 00:38 — so the final declared
intent keeps e1d70dd0 (see FALLBACK.md). The durable code fixes:

- bin/estate-reconcile: watcher never watches itself — SELF_BIN and LOG_DIR
  events skipped in cmd_watch; BREAKER OPEN body now canonical per path so
  repeats coalesce inside DEDUPE_WINDOW_S (600s).
- deploy/manifest.yaml: merge-conflict markers resolved (openfang-kernel note).

Commits (sovereign-projects origin/main, all ls-remote verified):
- ccba093871: script fix + herd bless (bless later superseded, see below)
- de600f0437: revert stale herd bless back to e1d70dd0 (FALLBACK-blessed)

Live verification: `estate-reconcile check` → OK (all 4 binaries, files +
running); herd daemon restarted via pitchfork onto the declared binary
(:25100 health OK); watch daemon restarted; alert flood coalesced to ~1
post per dedupe window.
