# MCP Infrastructure Audit Report

**Date:** 2026-07-20
**Audited by:** Sovereign Agent (Zed)

---

## Executive Summary

The Sovereign MCP stack has **two layers**: **mcpproxy** (`:25109`) handles all upstream MCP server connections for the Zed agent, and **sovereign-mcp-gateway** (`:25120`) sits as a trust boundary in front of upstream servers (currently only byte-vision). The infrastructure exposes **256+ tools** across **26 healthy MCP servers**. However, several backend services are down or misconfigured, and there are pending tool approvals blocking some capabilities.

---

## Architecture

```
Zed Agent
  │
  ├── mcpproxy (:25109) ─── orchestrates 29 MCP servers
  │     ├── agent-mcp-gateway (:25120)
  │     │     └── byte-vision-mcp (:25121)  [1 tool]
  │     ├── desktop-commander [26 tools]
  │     ├── ast-grep-nnunley [21 tools]
  │     ├── ghas [25 tools]
  │     ├── github [26 tools]
  │     ├── codebase-memory [14 tools]
  │     ├── computer-use-linux [18 tools]
  │     ├── redis-mcp [47 tools]
  │     ├── agent-orchestration [35 tools]
  │     ├── smarter-ast-mcp [8 tools]
  │     ├── safurrier-filesystem-smart [21 tools]
  │     ├── arxiv [10 tools, 2 pending]
  │     ├── arxiv-advanced [6 tools]
  │     ├── ast-grep-xray [4 tools]
  │     ├── context7 [2 tools]
  │     ├── mcp-background-job [7 tools]
  │     ├── prometheus [6 tools]
  │     ├── qdrant-mcp [4 tools]
  │     ├── sqlite-mcp [6 tools]
  │     ├── fetch [1 tool]
  │     ├── websearch-skill [5 tools]
  │     ├── markitdown [1 tool]
  │     ├── sequential-thinking-thin [1 tool]
  │     ├── tpc-thought-ledger [9 tools]
  │     └── llama-swap-test [5 tools, 5 pending]
  │
  └── Zed built-ins (terminal, read_file, edit_file, write_file, grep, find_path)
```

---

## Port Status (SSOT: `config/ports.env`)

| Port | Service | Status | Notes |
|------|---------|--------|-------|
| 25100 | llama-swap (mesh-front) | **LISTEN** | LLM proxy |
| 25101 | rust-web (mesh-front) | **LISTEN** | |
| 25102 | yote | **LISTEN** | |
| 25103 | openfang (mesh-front) | **LISTEN** | |
| 25104 | sovereign-router | **LISTEN** | |
| 25105 | prometheus | **DOWN** | Not listening; prometheus-mcp-server configured to this |
| 25106 | hf-downloader (mesh-front) | **LISTEN** | |
| 25107 | null-g | **LISTEN** | |
| 25108 | pitchfork | **DOWN** | Not listening (manages other services externally) |
| 25109 | mcpproxy | **LISTEN** | Zed agent MCP proxy |
| 25110 | grafana | **DOWN** | Not listening |
| 25111 | watchdog/sovereign_web | **LISTEN** | |
| 25112 | GHAS API | **LISTEN** | |
| 25115 | mesh-hub | **LISTEN** | |
| 25120 | sovereign-mcp-gateway | **LISTEN** | Trust boundary |
| 25121 | byte-vision-mcp | **LISTEN** | HTTP server up, but MCP stdio bridge broken |
| 25133 | qdrant | **DOWN** | qdrant-mcp configured but not listening |
| 6379 | redis | **LISTEN** | `redis-cli ping` → PONG |
| 3000 | Unknown (MainThread) | **LISTEN** | pid=2407 |

---

## Configuration File Locations

| File | Purpose |
|------|---------|
| `~/.config/zed/settings.json` | Zed agent MCP config (`mcpproxy-sovereign` → `:25109`, `wcgw`) |
| `~/.local/state/mcpproxy/mcp_config.json` | mcpproxy server registry (29 servers) |
| `~/.config/agent-mcp-gateway/.mcp.json` | agent-mcp-gateway config (context7, filesystem) |
| `~/sovereign/config/.mcp.json` | Project-level MCP config (computer-use-linux) |
| `~/sovereign/config/ports.env` | Port SSOT |
| `~/sovereign/tools/sovereign-router/sovereign-mcp-gateway/` | Gateway source (gateway.ts, gateway-core.ts, tests) |

---

## Server Health Detail

### Healthy Servers (26)

| Server | Tools | Protocol | Notes |
|--------|-------|----------|-------|
| agent-mcp-gateway | 3 | stdio | Gateway self-endpoints |
| agent-orchestration | 35 | stdio | Cursor delegation |
| arxiv | 10 | stdio | **2 tools pending approval** |
| arxiv-advanced | 6 | stdio | |
| ast-grep-nnunley | 21 | stdio | AST search/replace |
| ast-grep-xray | 4 | stdio | what_breaks analysis |
| codebase-memory | 14 | stdio | Knowledge graph |
| computer-use-linux | 18 | stdio | Screenshots, keyboard, desktop |
| context7 | 2 | stdio | Documentation lookup |
| desktop-commander | 26 | stdio | Terminal, file ops, processes |
| fetch | 1 | (auto) | URL fetching |
| ghas | 25 | stdio | GitHub code search |
| github | 26 | (auto) | GitHub API |
| llama-swap-test | 5 | stdio | **5 tools pending approval** |
| markitdown | 1 | stdio | Document conversion |
| mcp-background-job | 7 | stdio | Background commands |
| prometheus | 6 | stdio | Points to `:25105` (DOWN) |
| qdrant-mcp | 4 | stdio | Points to `:25133` (DOWN) |
| redis-mcp | 47 | stdio | Points to `:6379` (UP) |
| safurrier-filesystem-smart | 21 | stdio | Enhanced filesystem |
| sequential-thinking-thin | 1 | stdio | |
| smarter-ast-mcp | 8 | stdio | AI-enhanced code search |
| sqlite-mcp | 6 | stdio | `~/ast_matrix.db` |
| tpc-thought-ledger | 9 | stdio | |
| websearch-skill | 5 | stdio | |

### Disabled Servers (3)

| Server | Reason |
|--------|--------|
| hyprland-ipc | User-disabled |
| mise-mcp-server | User-disabled (uses deno, runs from remote URL) |
| vram-mcp | User-disabled |

### Unhealthy Servers (1)

| Server | Error | Retries |
|--------|-------|---------|
| byte-vision-llamacpp | `Module not found "/home/toxic/byte-vision-mcp/src/server.ts"` | 129 |

The byte-vision-mcp HTTP server IS listening on `:25121` but the MCP stdio bridge from mcpproxy is broken — the bun process can't find the module. The gateway (`:25120`) shows it as healthy because it caches from its last successful probe.

---

## Tool Categories Available

| Category | Servers | Total Tools |
|----------|---------|-------------|
| **Terminal/Process** | desktop-commander, mcp-background-job | ~40 |
| **Code Search/AST** | ast-grep-nnunley, ast-grep-xray, smarter-ast-mcp | ~33 |
| **GitHub/VCS** | ghas, github | ~51 |
| **Desktop Automation** | computer-use-linux | 18 |
| **Research** | arxiv, arxiv-advanced | ~16 |
| **Database** | redis-mcp, sqlite-mcp, qdrant-mcp | ~57 |
| **Documentation** | context7 | 2 |
| **Monitoring** | prometheus | 6 |
| **Knowledge Graph** | codebase-memory | 14 |
| **Filesystem** | safurrier-filesystem-smart | 21 |
| **Web/Fetch** | fetch, websearch-skill | 6 |
| **AI/Cognition** | sequential-thinking-thin, smarter-ast-mcp | ~9 |
| **Task Management** | agent-orchestration, tpc-thought-ledger | ~44 |
| **Document** | markitdown | 1 |
| **LLM Management** | llama-swap-test | 5 |

**Total: ~256 tools across 26 servers**

---

## Issues Found

### Critical

1. **byte-vision-llamacpp MCP bridge broken** — The stdio transport can't find `/home/toxic/byte-vision-mcp/src/server.ts`. The HTTP server on `:25121` responds but the MCP proxy chain is broken. 129 retries logged. The gateway still shows it as healthy (stale cache).

### High

2. **Prometheus backend down** — Port `:25105` not listening. The prometheus-mcp-server is configured to query `http://localhost:25105` which means all 6 prometheus tools will fail at query time even though the MCP server itself is "healthy."

3. **Qdrant backend down** — Port `:25133` not listening. The qdrant-mcp-server is configured to query `http://localhost:25133`. All 4 qdrant tools will fail.

4. **10 pending tool approvals** — 2 arxiv tools + 5 llama-swap-test tools + potentially others are blocked behind approval gates. These tools are discovered but not callable.

### Medium

5. **Grafana down** — Port `:25110` not listening. No MCP server references it, but it's in the port SSOT.

6. **Duplicate filesystem servers** — `safurrier-filesystem-smart` (in mcpproxy, 21 tools) AND `filesystem` (in agent-mcp-gateway .mcp.json) both provide filesystem access. The agent-mcp-gateway filesystem is a separate config layer.

7. **Duplicate context7** — Configured both in mcpproxy (via upstream_servers) and in `~/.config/agent-mcp-gateway/.mcp.json`.

8. **Sovereign-mcp-gateway underutilized** — Only proxies 1 upstream (byte-vision) for 1 tool. The gateway's circuit breaker + sticky affinity architecture is designed for multiple upstreams but only has one, and that one is broken.

### Low

9. **3 servers disabled** — hyprland-ipc, mise-mcp-server, vram-mcp. These may be intentionally disabled but represent missing capabilities.

10. **Docker isolation unavailable** — Docker is not detected on the host, so no MCP servers can run in Docker containers.

---

## Recommendations for Maximal Setup

### Immediate Fixes

1. **Fix byte-vision-mcp** — Either:
   - Restore `/home/toxic/byte-vision-mcp/src/server.ts` (check if the repo was moved/deleted)
   - Update the mcpproxy server command to point to the correct path
   - Or remove the broken entry if byte-vision is no longer needed

2. **Start Prometheus** — `pitchfork start prometheus` or ensure it's in the pitchfork config

3. **Start Qdrant** — If vector search is needed, start the qdrant service

4. **Approve pending tools** — Use `quarantine_security` with `operation: "approve_all_tools"` for arxiv and llama-swap-test, or approve individually

### Architecture Improvements

5. **Expand sovereign-mcp-gateway upstreams** — Instead of only proxying byte-vision, consider routing more sensitive MCP servers through the gateway for circuit breaking + audit. Currently mcpproxy handles all the real connections.

6. **Remove duplicate servers** — Consolidate the duplicate context7 and filesystem configs. The agent-mcp-gateway `.mcp.json` seems to be a separate config layer that may conflict with mcpproxy.

7. **Enable useful disabled servers** — Consider enabling:
   - `hyprland-ipc` — Window management automation
   - `mise-mcp-server` — Task management (if deno is available)
   - `vram-mcp` — GPU monitoring

8. **Add missing capabilities** — Potential additions:
   - **Browser automation** — Playwright MCP (already in grok configs)
   - **Calendar/Email** — If needed for agent autonomy
   - **Docker management** — When Docker becomes available
   - **System monitoring** — node-exporter metrics through prometheus

### Security

9. **Review quarantined tools** — Currently 0 quarantined, which is clean. Maintain this discipline.

10. **API key management** — The `CONTEXT7_API_KEY` is hardcoded in two config files. Consider using environment variables.

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total MCP servers configured | 29 |
| Healthy/enabled | 26 |
| Disabled | 3 |
| Unhealthy | 1 (byte-vision) |
| Total tools discovered | ~256 |
| Pending tool approvals | 10+ |
| Sovereign ports listening | 11 of 16 defined |
| Services down | prometheus, grafana, qdrant, pitchfork (UI) |
| Quarantined servers | 0 |
| Quarantined tools | 0 |
