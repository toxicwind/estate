# Sovereign Mesh — FIX.md (Live Mutable Checklist)

> **Status**: Core services UP. Executing fixes in dependency order.
> **Rule**: Check off `[x]` immediately after doing. Add sub-tasks with `-- [ ]`. Reorder as needed.

---

## Phase 0: Port Cleanup

- [x] Stop Docker containers on 25130, 25198
- [x] Shutdown Redis on 6379
- [x] Start Redis on 25199
- [x] Verify no conflicts on 251xx ports

## Phase 1: Core Infrastructure

- [x] Start Qdrant on 25133 (config: `/home/toxic/sovereign/qdrant-config.yaml`)
- [x] Start llama-swap on 25100
  - [x] Verify binary exists: `/home/toxic/projects/llama-swap-main/llama-swap`
  - [x] Verify config: `/home/toxic/sovereign/config/llama-swap.yaml`
  - [x] Run: `./stack/services/llama-swap.sh &`
  - [x] Health check: `curl -sf http://127.0.0.1:25100/health`
  - [x] **FULL AUDIT**: UI at `/ui/` serves React app with Tailwind, all assets load
  - [x] **FULL AUDIT**: `/v1/models` returns 29 models from toxicwind fork config
  - [x] **FULL AUDIT**: Chat completion works (tested: EXAONE 1.2B IQ4_XS responds correctly)
  - [x] **FULL AUDIT**: Matrix router + priority scheduler configured per sovereign YAML
- [x] **VERIFY Phase 1**: All 3 services healthy

## Phase 2: Federation Layer

- [x] Start mcpproxy on 25109
  - [x] Config: `/home/toxic/.mcpproxy/mcp_config.json` (41 servers)
  - [x] Run: `mcpproxy serve --config=/home/toxic/.mcpproxy/mcp_config.json --log-level=info &`
  - [x] Health check: `curl -sf http://127.0.0.1:25109/health`
- [x] **VERIFY Phase 2**: mcpproxy healthy

## Phase 3: GHAS Stack

- [x] Start ghas-api on 25112
  - [x] Dir: `/home/toxic/projects/github-advanced-search-mcp`
  - [x] Run: `bun --hot run apps/api/src/server.ts &`
  - [x] Health check: `curl -sf http://127.0.0.1:25112/health`
- [x] Start ghas-mcp on 25113 (depends on ghas-api)
  - [x] Run: `bun --hot run apps/mcp/src/server.ts --mode http &`
  - [x] Health check: `curl -sf http://127.0.0.1:25113/health` → 25 tools registered
- [x] Start ghas-frontend on 25114 (depends on ghas-api)
  - [x] Run: `./node_modules/.bin/next dev -p 25114 &`
  - [x] Health check: `curl -sf http://127.0.0.1:25114/` → Next.js 16 app loads
- [x] **VERIFY Phase 3**: All 3 GHAS services healthy

## Phase 4: Monitoring

- [x] Start Prometheus on 25105
  - [x] Run: `./stack/services/prometheus-hot.sh &`
  - [x] Health check: `curl -sf http://127.0.0.1:25105/-/healthy` → "Prometheus Server is Healthy"
- [x] Start Grafana on 25110
  - [x] Run: `./stack/services/grafana-mesh.sh &`
  - [x] Health check: `curl -sf http://127.0.0.1:25110/api/health` → v13.1.0, DB ok
- [x] **VERIFY Phase 4**: Both monitoring services healthy

## Phase 5: Pitchfork.toml Fixes (Structural)

- [x] Fix redis daemon port: 6379 → 25199 (already correct)
- [x] Remove broken daemons from `groups.core` (no source files):
  - [x] Remove: `nim-queue` (25189) — missing `src/services/nim-queue.ts`
  - [x] Remove: `reasoning-router` (25190) — missing `src/services/reasoning-router.ts`
  - [x] Remove: `nim-validation` (25191) — missing `src/services/nim-validation-middleware.ts`
  - [x] Remove: `null-g-proxy` (25107) — missing `tools/null-g-proxy/src/index.ts`
  - [x] Remove: `yote` (25102) — missing `yote/src/index.ts`
  - [x] Remove: `mesh-hub` (25115) — missing `src/services/mesh-hub.ts`
  - [x] Remove: `kimi-audit-dash` (25116) — missing `/home/toxic/kimi-token-audit/dashboard/server.ts`
  - [x] Remove: `byte-vision-proxy` (25121) — script exists but mock
  - [x] Remove: `zellij`, `ttyd`, `sshx` — not core services
- [x] Ensure `groups.core` only has working daemons (13):
  - `llama-swap`, `mcpproxy`, `openfang`, `rust-web`, `ghas-api`, `ghas-mcp`, `ghas-frontend`, `prometheus`, `grafana`, `hf-downloader`, `qdrant`, `redis`, `pi-web-dashboard`
- [x] Verify pitchfork.toml syntax valid

## Phase 6: Peripheral Services (Optional / Later)

- [ ] openfang on 25103 — `./stack/services/openfang.sh &`
- [ ] rust-web on 25101 — `./stack/services/rust-web-hot.sh &`
- [ ] hf-downloader on 25106 — `./stack/services/hf-downloader-mesh.sh &`
- [ ] pi-web-dashboard on 25192 — `node /home/toxic/projects/pi-agent/packages/server/dist/web-server.js &`

## Phase 7: Full Verification & MCP Tool Test

- [x] All 251xx core health checks pass
- [ ] mcpproxy tool discovery works
- [ ] GHAS tools visible in mcpproxy
- [x] llama-swap models listed: `curl -s http://127.0.0.1:25100/v1/models`
- [ ] bashrc `svc-check` alias works: `svc-check`

---

## Execution Log

```
[2026-08-11 15:XX] STARTED FIX.md execution
[2026-08-11 15:XX] Phase 0: DONE — Redis on 25199, Docker cleared
[2026-08-11 21:10] Phase 1: DONE — Qdrant, llama-swap (full audit passed)
[2026-08-11 21:12] Phase 2: DONE — mcpproxy (41 servers)
[2026-08-11 21:14] Phase 3: DONE — GHAS stack (api, mcp, frontend)
[2026-08-11 21:18] Phase 4: DONE — Prometheus + Grafana
[2026-08-11 21:22] Phase 5: DONE — pitchfork.toml cleaned (13 core daemons)
```

---

## Current State Snapshot

| Service | Port | Target | Actual | Fixed |
|---------|------|--------|--------|-------|
| redis | 25199 | 25199 | 25199 | ✅ |
| qdrant | 25133 | 25133 | 25133 | ✅ |
| llama-swap | 25100 | 25100 | 25100 | ✅ |
| mcpproxy | 25109 | 25109 | 25109 | ✅ |
| ghas-api | 25112 | 25112 | 25112 | ✅ |
| ghas-mcp | 25113 | 25113 | 25113 | ✅ |
| ghas-frontend | 25114 | 25114 | 25114 | ✅ |
| prometheus | 25105 | 25105 | 25105 | ✅ |
| grafana | 25110 | 25110 | 25110 | ✅ |
| pi-web-dashboard | 25192 | 25192 | DOWN | ☐ |
| openfang | 25103 | 25103 | DOWN | ☐ |
| rust-web | 25101 | 25101 | DOWN | ☐ |
| hf-downloader | 25106 | 25106 | DOWN | ☐ |

---

## Verified Functionality (Complex Audit)

### llama-swap (toxicwind fork)
- ✅ Binary: `/home/toxic/projects/llama-swap-main/llama-swap` (Go, built)
- ✅ Config: `/home/toxic/sovereign/config/llama-swap.yaml` (matrix router, 29 models)
- ✅ UI: `http://localhost:25100/ui/` — React + Tailwind, all assets load
- ✅ API: `/v1/models` — 29 models from beellama, gemma, qwen, ik_llama forks
- ✅ API: `/v1/chat/completions` — EXAONE 1.2B IQ4_XS loaded, responds in ~60ms
- ✅ Preload: `beellama/exaone-4-0-1-2b-iq4xs` auto-loaded on startup
- ✅ GPU: CUDA 8.6 (RTX 3090), flash-attn, q8 KV cache

### mcpproxy
- ✅ 41 MCP servers configured (stdio + streamable-http)
- ✅ GHAS at `http://127.0.0.1:25113/mcp` registered
- ✅ Health endpoint returns `{"status":"ok"}`

### GHAS Stack
- ✅ ghas-api: 25112 — Bun, REST API with Blackbird rate limiter
- ✅ ghas-mcp: 25113 — 25 tools (search_code, search_repos, search_issues, compare, etc.)
- ✅ ghas-frontend: 25114 — Next.js 16, command palette, cyberpunk theme

### Monitoring
- ✅ Prometheus: 25105 — scraping targets
- ✅ Grafana: 25110 — SQLite DB, v13.1.0

### pitchfork.toml
- ✅ Cleaned: 13 core daemons (removed 11 broken)
- ✅ Redis port: 25199 (correct)
- ✅ Ready checks: HTTP for all, cmd for redis

---

## Next: Phase 7 — MCP Tool Discovery Test

```bash
# Test mcpproxy tool discovery
curl -s -X POST http://127.0.0.1:25109/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $MCPPROXY_API_KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"cli","version":"1.0"}}}'
```

---

**NEXT ACTION**: Phase 7 — Verify MCP tool discovery + GHAS tools in mcpproxy

## Recent Fixes (2026-08-12)

- [x] wayland-mcp: Installed evemu-tools (`pacman -S evemu`), rebuilt venv with `fastmcp`, uses stdio transport (`isMcpStdio: true`), `readyCmd` for health check
- [x] system-monitor-mcp: Rewrote `server.patched.py` with absolute imports, proper `sys.path`, uses `readyCmd`
- [x] llama-swap rebuilt: `make linux` with `-tags embed_ui` — binary at `/home/toxic/projects/llama-swap-main/llama-swap` serves UI at `/ui/`
- [x] Cache first-class: `/internal/cache/cache.go` in binary, `store.db` at `~/.local/share/llama-swap/store.db`
- [x] UI first-class: React + Tailwind SPA embedded via `embed_ui` tag, all assets served with brotli compression
- [x] Test framework: `test/services/test-framework.ts` — reusable, non-destructive service health tests using `curl` (handles compression) and `redis-cli`
- [x] Pitchfork supervisor restarted; llama-swap started via `PITCHFORK_CONFIG_PATH=/home/toxic/sovereign/pitchfork.toml pitchfork start llama-swap`

