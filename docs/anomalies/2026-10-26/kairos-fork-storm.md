# 2026-10-26 ~02:09 — system-wide SSH lag (load 4004)

## Symptoms
- SSH lagging, everything on the box slow. Snapshot commands took 20–27s.
- Load average **4004** (8 cores). RAM 59Gi/62Gi used + 31Gi swap wedged.
- R-state threads: 932 `bun`, 591 `mi-scavenger` (mimalloc scavenger = bun children).

## Culprit
**9,439 processes**, all identical:
```
bun run /home/toxic/pens/ranch/kairos/src/cli.ts run bun run \
  /home/toxic/pens/olympus/products/kairos/skills/pattern-forge/bin/forge.ts \
  borrow bun global install symlink archive
```
Mixed ages (fresh spawns every few seconds + 1h45m-old wedged ones), orphans re-parented to PID 1.

## Root cause — shim re-entry recursion (guard was dead code)
1. `bun:run` is in `SLOW_ROUTES` → shim `bun()` routes every `bun run` to `run-fast` (kairos).
2. kairos runner spawns `/bin/bash -o pipefail -c "bun run …"` children **with `BASH_ENV` intact**.
3. Child bash sources the shim → `bun()` wraps the same `bun run` again → `run-fast` → ∞.
4. `runner.ts:384` sets `RUN_FAST_ACTIVE=1` on children — comment even describes this exact
   incident ("observed: gh api spawning hundreds of kairos run children") — **but the shim
   never checked it.** Guard existed only as dead code.

## History
- **Second recurrence tonight.** The 04:50 session (`2026-10-26T04-50-10-397Z`) found the same
  storm (5,143 procs, load 3666), killed the swarm, identified the suspected racer self-feed —
  but never fixed the shim, so it grew back.

## Fix (kairos `09a49d7`, pushed to toxicwind/kairos)
- `_2s_slow()` in the shim generator SSOT (`pens/olympus/products/kairos/src/init.ts`) now begins:
  `[ -n "${RUN_FAST_ACTIVE:-}" ] && return 1` → children under run-fast use the REAL binary.
- `timeout()` wrapper guarded identically (it bypasses `_2s_slow` and went straight to `RF_BIN`).
- Regenerated BOTH shim copies: olympus product (sourced by `.bashrc`) and the ranch mirror
  (`pens/ranch/kairos/shim.sh`, execed by run-fast via `KAIROS_SRC`).

## Verification
- `bash -n` both regenerated shims: OK.
- `RUN_FAST_ACTIVE=1 _2s_slow bun run` → rc 1 (real binary); unset → rc 0 (slow-route). PASS.
- `RUN_FAST_ACTIVE=1 timeout 1 echo hi` → ran real `timeout`, rc 0. PASS.
- Post-kill: RAM 59Gi→12Gi used, R-state threads ~1–4, command latency 24s→0.2s,
  load decaying 4004→51 (1-min decay metric; runnable-thread count is the true signal).

## Lesson
- Kill-sweeps without fixing the spawner = the storm returns. Fix the guard, then sweep.
- Load average decays for minutes; judge recovery by R-state thread count + latency.
