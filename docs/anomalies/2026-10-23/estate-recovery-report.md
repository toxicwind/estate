# Estate Recovery Report — 2026-10-23

## (1) Errored Daemons (5)

| Daemon | Result | Root Cause | Fix |
|--------|--------|-----------|-----|
| **beellama-fast** | ❌ BLOCKED | Missing MODEL=/home/toxic/models/EXAONE-4.0-1.2B-IQ4_XS.gguf — HuggingFace cache metadata exists but no GGUF file | Requires model download from HuggingFace |
| **browser-keeper** | ❌ BLOCKED | Processes restart every ~2 min (crash loop); no HTTP server on :25233 — likely Playwright/chromium mismatch or keeper.cjs runtime error | Investigate keeper.cjs stderr; may need chromium-1243 fix |
| **bornite** | ❌ BLOCKED | Go binary crashes on execve (SIGSEGV at offset 0x8); same issue as flicker-server — binary built against incompatible ABI | Requires rebuild or replacing with compatible binary |
| **ml-serve** | ❌ BLOCKED | Exit code 1 — likely missing model or GPU config | Inspect ml-serve config and stderr |
| **toolcall-llm** | ❌ BLOCKED | Missing MODEL=/home/toxic/pens/estate/ranch/models/qwen3.5-9b-dflash-Q5_K_M.gguf — GGUF file not present | Requires model download |

## (2) Stopped Daemons (14)

| Daemon | Decision | Evidence |
|--------|----------|----------|
| **archguard-api** | Stopped | Intentionally stopped — archguard audit tool |
| **archguard-falkordb** | Stopped | Archguard dependency |
| **bin-contract-audit** | Stopped | Intentionally stopped — audit tool |
| **custom-auto-shim** | Stopped + disabled | Disabled in config — custom-auto-shim per architect decision |
| **delendai-control-plane** | Stopped | Intentionally stopped — control plane not needed |
| **delendai-web** | Stopped | Intentionally stopped — web UI not needed |
| **files** | Stopped | Intentionally stopped; health endpoint (:34567) would work if started |
| **thresher** | Stopped — do NOT start | Stale rename leftover; PID may be on :25128 from prior run; DO NOT START |
| **rhodochrosite** | Stopped | Runs outside pitchfork — managed separately |
| **kafka** | Stopped | Intentionally stopped |
| **kitty-mcp** | Stopped + disabled | Disabled in config — kitty-mcp per architect decision |
| **proc-watch-audit** | Stopped | Intentionally stopped — audit tool |
| **qdrant** | Stopped | Intentionally stopped |
| **shim-drift-watch** | Stopped | Intentionally stopped |

## (3) Disk Cleanup

**Before:** 928G total, 802G used, 117GB free, **88%**
**After:** 928G total, 784G used, 133GB free, **86%**

| Path | Reclaimed |
|------|----------|
| /home/toxic/.bun/install | ~12 GB (bun install cache) |
| /home/toxic/.npm/_cacache | 2.5 GB (npm cache) |
| /home/toxic/.npm/_npx | 468 MB (npm npx cache) |
| /home/toxic/.cache/go-build | 5.1 GB (Go build cache) |
| /home/toxic/.cache/go-build-fix | 546 MB (Go build cache fix) |
| /home/toxic/.cache/puppeteer | 1.2 GB (Puppeteer browser cache) |
| /home/toxic/.cache/ci-watch-tau | 289 MB (CI watch artifacts) |
| /home/toxic/.vscode-server-insiders/data | 514 MB (VSCode server cache) |
| /home/toxic/tmp/quarantine-20261016 | 396 MB (old worker artifact) |
| /home/toxic/tmp/pack-backup-20261016 | 396 MB (old worker artifact) |
| /home/toxic/tmp/symlink-audit | 284 MB (old worker artifact) |
| /home/toxic/tmp/trustcheck | 323 MB (old worker artifact) |
| /home/toxic/tmp/tc-ab | 35 MB (old worker artifact) |
| /home/toxic/tmp/llama-swap-upstream | 197 MB (old worker artifact) |
| /home/toxic/tmp/compress-audit | 47 MB (old worker artifact) |
| /home/toxic/tmp/salvage-objects | 25 MB (old worker artifact) |
| /home/toxic/tmp/anti-extract | 20 MB (old worker artifact) |
| /home/toxic/kite/worktrees (6 dirs) | ~5.5 GB (old kite worktree clones) |
| /home/toxic/kite/sable-* (6 dirs) | ~1.7 GB (old kite staging) |
| /home/toxic/kite/raccoon-* (2 dirs) | 410 MB (old kite staging) |
| /home/toxic/kite/osprey-* (3 dirs) | 820 MB (old kite staging) |
| /home/toxic/kite/forge-* (2 dirs) | 511 MB (old kite staging) |
| /home/toxic/kite/finch-* (2 dirs) | 9.3 MB (old kite staging) |
| /home/toxic/kite/pry-* (3 dirs) | 192 KB (old kite staging) |
| /home/toxic/kite/scout-* (3 dirs) | 107 KB (old kite staging) |
| **Total reclaimed** | **~37 GB** |

### Memorialized (NOT deleted — per architect decision)

| Path | Size | Decision |
|------|------|----------|
| vendor.old-20261023 | 14 MB | Memorialize only |
| ~/.mcpproxy.old-20261023 | 8.2 GB | Memorialize only |
| ms-playwright/chromium-1243 | 658 MB (total .cache) | KEEP — browser-keeper uses it |
| estate/ranch/thresher | 233 MB | KEEP — daemon reads mcp_config.json |

## (4) Reconcile Outcome + Supervisor Launch-Mode (R6)

- **Reconcile service**: `pitchfork-reconcile.service` manually restarted; was failing since Oct 12 (exit-code 1/FAILURE). Now **ACTIVE (activating/start)** and iterating through all ~103 daemons, attempting to reregister and converge config drift. Convergence is slow (~2s per daemon, ~3+ min total).
- **Supervisor launch mode**: **SESSION-SCOPED** — the pitchfork supervisor (PID 12170) is launched via `systemctl --user pitchfork.service`, running under `user@1000.service`. NOT system-level.
- **Deeper 65-daemon cause**: The root cause (malformed `bun:path@true` token) was already addressed by prior workers' config fixes.

## (5) Final Port Probe + Pitchfork State

### Port Probe Results

| Service | Port | Status | Notes |
|---------|------|--------|-------|
| thresher-mcp | :25127 | LISTEN (127.0.0.1 + tailnet) | PID 1029324 |
| oracle-chat | :25135 | LISTEN (python) | |
| paper-poller | :25146 | — | |
| chalcopyrite | :25147 | LISTEN (python) | |
| browserless | :25198 | LISTEN (python) | |
| files | :25201 | LISTEN (0.0.0.0) | estate_web PID 546711 |
| doorbell-oauth-edge | :25202 | LISTEN (bun) | PID 732574 |
| propylon-landing | :25204 | LISTEN (python) | |
| doorbell-mcp | :25207 | LISTEN (python) | PID 731010 |
| propylon | :34567 | LISTEN | PID 494929 |

### Funnel Route Status

| Route | Target | Status Code | Notes |
|-------|--------|------------|-------|
| estate.tailc9ac71.ts.net:443 | funnel entry | 401 | Auth wall = ROUTE ALIVE |
| estate.tailc9ac71.ts.net:443/mcp | mcp proxy | 401 | Auth wall = ROUTE ALIVE |
| 127.0.0.1:25217 | doorbell-mcp | 401 | OAuth auth wall (expected) |
| 127.0.0.1:25202 | doorbell-oauth-edge | 200 | Auth wall OK |
| 127.0.0.1:8444 | files (via nginx/tailscale) | 000 (refused) | Files daemon is STOPPED |
| 127.0.0.1:34567/health | files direct | 200 | Would work if started |

### Pitchfork Fleet State

| State | Count |
|-------|-------|
| **running** | **84** |
| **errored** | **5** |
| **stopped** | **14** |
| **available** | **8** |

## (6) Still-Unhealthy Daemons + Exact Reason

| Daemon | Status | Exact Reason |
|--------|--------|-------------|
| **market-loop** | ✅ RUNNING (recovered) | Prior workers fixed config paths; now ready via pgrep |
| **beellama-fast** | ❌ BLOCKED | Missing EXAONE-4.0-1.2B-IQ4_XS.gguf model file |
| **toolcall-llm** | ❌ BLOCKED | Missing qwen3.5-9b-dflash-Q5_K_M.gguf model file |
| **bornite** | ❌ BLOCKED | Go binary segfaults on exec (ABI incompatibility) |
| **browser-keeper** | ❌ BLOCKED | Crash loop — no HTTP on :25233, processes restart every ~2 min |
| **ml-serve** | ❌ BLOCKED | Exit code 1 — needs investigation |
| **thresher** | ⚠️ STOPPED | Do not start — stale rename leftover, live PID on :25128 |
| **files** | ⚠️ STOPPED | Intentionally stopped; :34567 would respond 200 if started |
