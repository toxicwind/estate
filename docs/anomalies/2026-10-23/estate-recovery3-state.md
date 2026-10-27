# Phase 1+2 Checkpoint — State Verification, Config Edits + Restart Results

## Pitchfork List Summary (2026-10-23)

- **running**: 56 daemons (+3 from Phase 1's 53: keypool, browser-keeper, phone-sentinel)
- **errored**: 8 daemons (down from 11: beellama-fast, chalcopyrite, forge, forge-agent, bornite, market-loop, oracle-core, toolcall-llm)
- **stopped**: 14 daemons (unchanged)
- **available**: 8 daemons (unchanged)
- Full list output: `/home/toxic/tmp/estate-recovery3-list.txt`

## Phase 1 — Config Edits Verified/Fixed

| File | What Changed | Verified Target Exists? |
|------|-------------|------------------------|
| `pitchfork.toml` browser-keeper | run: bin/keeper.ts → keeper.cjs (via bun run keeper in ranch/keeper), port 25154→25157, dir set to keeper root | ✅ keeper.cjs exists |
| `pitchfork.d/browser-keeper.toml` | Same fix (port 25157, run via bun run keeper) | ✅ |
| `pitchfork.toml` keypool | run: `/home/toxic/estate/services/keypool/` → `/home/toxic/estate/var/workspaces/layout/ranch/mesh/keypool/` | ✅ index.ts exists |
| `pitchfork.d/keypool.toml` | Already had correct path (prior workers fixed) | ✅ |
| `pitchfork.toml` market-loop | run: `/home/toxic/estate/agents/weaver/bin/` → `/home/toxic/estate/var/workspaces/layout/estate/agents/weaver/bin/` | ✅ market-loop.ts exists |
| `pitchfork.d/market-loop.toml` | Already had correct path | ✅ |
| `pitchfork.toml` forge | port 25148→25150, WOODPECKER env refs updated | ✅ flicker-server exists |
| `pitchfork.d/forge.toml` | Already had port 25150 | ✅ |
| `pitchfork.d/oracle-core.toml` | Port reverted 25151→25149 (collision with paper-poller), then updated in Phase 2 to 25235 | ✅ run-oracle-core.sh exists |
| `pitchfork.toml` oracle-core | Port updated 25151→25235 + env ORACLE_CORE_LISTEN | ✅ |
| `pitchfork.d/thresher.toml` | run: `/home/toxic/estate/ranch/range/bin/` → `/home/toxic/estate/var/workspaces/layout/ranch/range/bin/` | ✅ exists; thresher NOT started (live PID on :25128) |
| `pitchfork.d/bornite.toml` | Already correct: depends=[thresher] (not thresher) | ✅ |
| `pitchfork.toml` phone-sentinel | run: `bun run` → `exec /home/toxic/.bun/bin/bun run` (pin correct bun) | ✅ |
| `pitchfork.toml` browser-keeper | Port 25157→25233 (25157 taken by nativelink), health/ready/env updated | ✅ |
| `pitchfork.d/browser-keeper.toml` | Port updated 25157→25233 | ✅ |
| `pitchfork.toml` forge | Port 25150→25234 (25150 taken by python3), health/env updated | ✅ |
| `pitchfork.d/forge.toml` | Port updated 25234, health URLs still reference 25150 (needs sync) | ⚠️ health URLs still at 25150 in pitchfork.d |

## Phase 2 — Restart Results

| Daemon | Result | Cause/Notes |
|--------|--------|-------------|
| **keypool** | ✅ running on :25109 | Path fixed, started successfully |
| **phone-sentinel** | ✅ running on :25178 | Bun path pinned, started successfully |
| **browser-keeper** | ✅ running on :25233 | Reaped 22 stale chromium processes; PLAYWRIGHT_CHROMIUM_EXECUTABLE needs chromium-1243 but browser launched on chromium-1223 (mismatch — will crash on next relaunch). Still RUNNING. |
| **beellama-fast** | ❌ BLOCKED on model | `MODEL=/home/toxic/models/EXAONE-4.0-1.2B-IQ4_XS.gguf` missing. HuggingFace cache metadata exists but no actual GGUF file. Requires model download. |
| **toolcall-llm** | ❌ BLOCKED on model | `MODEL=/home/toxic/estate/ranch/models/qwen3.5-9b-dflash-Q5_K_M.gguf` missing. No matching GGUF found in estate/ranch/models. |
| **market-loop** | ❌ blocked on missing module | `Cannot find module '/home/toxic/projects/trading-post/src/market/index.ts'` — depends on `projects/trading-post` workspace which doesn't exist. Module resolution failure loops. |
| **oracle-core** | ❌ blocked on port collision | `OSError: Address already in use` on 25235 — something holds that port. The env ORACLE_CORE_LISTEN env var is set correctly but the daemon keeps retrying and failing. Need to find what's on 25235. |
| **bornite** | ❌ blocked on binary crash | Go binary at `pens/geode/products/bornite/bornite` segfaults on start (exit code 139). Binary is corrupted or built for wrong architecture. Config and bornite.sh path are correct. |
| **forge** | ❌ blocked on port collision | Port 25234 taken by something (unknown process). The health check `http://127.0.0.1:25234/api/health` never returns 2xx. Need to check what occupies 25234. |
| **forge-agent** | ❌ unknown | Binary exists at `pens/ranch/forge/flicker/bin/flicker-agent` but daemon exits with "unknown exit code" and no delay completes. May be blocked on WOODPECKER_SERVER connection. |
| **chalcopyrite** | ❌ blocked on missing deps | `Cannot find package 'memoirist'` — had pino installed but also needs `memoirist`. More deps missing. |

## Blocked Summary

| Daemon | Block Reason | Fix Required |
|--------|-------------|--------------|
| beellama-fast | Missing EXAONE-4.0-1.2B-IQ4_XS.gguf model | Download model |
| toolcall-llm | Missing qwen3.5-9b-dflash-Q5_K_M.gguf model | Download model |
| market-loop | Missing trading-post/src/market/index.ts | Install dependency or fix import path |
| oracle-core | Port 25235 occupied | Find and resolve port conflict |
| forge | Port 25234 occupied | Find and resolve port conflict |
| bornite | Binary segfaults (exit 139) | Rebuild or replace bornite binary |
| forge-agent | Unknown exit — WOODPECKER connection? | Diagnose after forge starts |
| chalcopyrite | Missing memoirist package | `bun install` in chalcopyrite |

## What Remains for Phase 3

1. **Port conflict resolution**: Check what owns 25234 (forge) and 25235 (oracle-core)
2. **Market-loop**: Fix import path or install trading-post workspace
3. **Chalcopyrite**: Install memoirist dependency
4. **Bornite**: Rebuild or replace the segfaulting Go binary
5. **Browser-keeper**: Fix PLAYWRIGHT_CHROMIUM_EXECUTABLE mismatch (1223 vs 1243) — will crash on next relaunch cycle
6. **Beellama-fast & toolcall-llm**: Download required model files
7. **Forge-agent**: Diagnose after forge starts
8. **Disk cleanup**: 96% used, 43GB free
9. **pitchfork-reconcile.service**: Manual restart needed after config fixes
10. **pitchfork.d/forge.toml**: Sync health URLs from 25150 to 25234

## Output Files

- `/home/toxic/tmp/estate-recovery3-list.txt` — full pitchfork list
- `/home/toxic/tmp/estate-recovery3-start-*.txt` — initial start outputs
- `/home/toxic/tmp/estate-recovery3-restart-*.txt` — restart outputs
- `/home/toxic/tmp/estate-recovery3-state.md` — this file
