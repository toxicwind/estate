# Estate Map

**GENERATED FILE — do not hand-edit.** Rebuild with `bun projects/ops/bin/estate-map.ts`;
drift-check with `bun projects/ops/bin/estate-map.ts --check`.

Generated 2026-10-02T12:36:59.931Z on `awrawr-pc`. Estate root `/home/toxic/estate`.

> **One word, one referent.** `estate/` is the control-plane tree. `ranch/` is the inference
> monorepo. The agent engine config lives in `~/.tau`. Every daemon runs out of the path
> pitchfork names — check `repos[]` below before editing anything.

## Where things actually live

| Repo | Path | Remote | Head | Committed | Dirty | Checkout kind |
|---|---|---|---|---|---|---|
| 🟢 **estate** | `/home/toxic/estate` | https://github.com/toxicwind/sovereign-projects.git | 4820dfca5e | 2026-10-02T06:35:46 | 66 | nested |
| 🟢 **ranch** | `/home/toxic/estate/ranch` | https://github.com/toxicwind/ranch | 6a4640f | 2026-10-02T06:33:45 | 320 | nested |
| 🟢 **ranch** | `/home/toxic/ranch` | https://github.com/toxicwind/ranch | 6a4640f | 2026-10-02T06:33:45 | 320 | nested |
| 🟢 **tau-config** | `/home/toxic/.tau` | — | — | — | 0 | none |

- **estate** (`/home/toxic/estate`) — control plane: pitchfork.toml, config/, bin/, bridge/, agents/, docs/, projects/
- **ranch** (`/home/toxic/estate/ranch`) — the inference estate monorepo: herd, flock, gatehouse, squawk, oracle, flicker, roost
- **ranch** (`/home/toxic/ranch`) — SECOND checkout of toxicwind/ranch — duplicate, not the daemon target
- **tau-config** (`/home/toxic/.tau`) — coding-agent engine config (config.yml, models.yml, model-router.json, mcp.json)

## Live services

| Port | SSOT | Pitchfork daemon | Live | Process |
|---|---|---|---|---|
| 22 | — | — | 🟢 | — |
| 53 | — | — | 🟢 | — |
| 443 | — | — | 🟢 | — |
| 631 | — | — | 🟢 | — |
| 3000 | — | — | 🟢 | flicker-agent |
| 4222 | — | — | 🟢 | nats-server |
| 4223 | — | — | 🟢 | nats-server |
| 5000 | FLEET_POWER_INTERVAL | — | ⚪️ | — |
| 5037 | — | — | 🟢 | adb |
| 5355 | — | — | 🟢 | — |
| 5432 | — | — | 🟢 | — |
| 5433 | — | — | 🟢 | postgres |
| 5900 | — | agent-display | 🟢 | Xvnc |
| 6080 | — | agent-viewer | 🟢 | websockify |
| 8000 | — | — | 🟢 | — |
| 8222 | — | — | 🟢 | nats-server |
| 8443 | — | — | 🟢 | — |
| 9093 | — | — | 🟢 | — |
| 9223 | — | browser-keeper | 🟢 | chrome |
| 18384 | — | — | 🟢 | syncthing |
| 18788 | — | — | 🟢 | MainThread |
| 18789 | — | — | 🟢 | MainThread |
| 18924 | — | — | 🟢 | — |
| 20128 | VANSROUTER_PORT | vansrouter | 🟢 | next-server (v1 |
| 20128 | VANSROUTER_PORT | vansrouter | 🟢 | next-server (v1 |
| 22000 | — | — | 🟢 | syncthing |
| 25017 | — | — | 🟢 | llama-server |
| 25100 | HERD_PORT | herd | 🟢 | llama-swap |
| 25100 | HERD_PORT | herd | 🟢 | llama-swap |
| 25101 | MODEL_GUARD_PORT | model-guard | 🟢 | python3 |
| 25101 | MODEL_GUARD_PORT | model-guard | 🟢 | python3 |
| 25102 | YOTE_PORT | yote | 🟢 | bun |
| 25102 | YOTE_PORT | yote | 🟢 | bun |
| 25103 | OPENFANG_PORT | openfang-front | 🟢 | bun |
| 25103 | OPENFANG_PORT | openfang-front | 🟢 | bun |
| 25104 | — | sovereign-router | 🟢 | bun |
| 25105 | PROMETHEUS_PORT | prometheus | 🟢 | bun |
| 25105 | PROMETHEUS_PORT | prometheus | 🟢 | bun |
| 25106 | HF_DOWNLOADER_PORT | hf-downloader | 🟢 | bun |
| 25106 | HF_DOWNLOADER_PORT | hf-downloader | 🟢 | bun |
| 25107 | NULL_G_PORT | null-g-proxy | 🟢 | bun |
| 25107 | NULL_G_PORT | null-g-proxy | 🟢 | bun |
| 25108 | WATCHDOG_PORT | — | 🟢 | sovereign_web |
| 25108 | WATCHDOG_PORT | — | 🟢 | sovereign_web |
| 25109 | KEYPOOL_PORT | keypool | 🟢 | bun |
| 25109 | KEYPOOL_PORT | keypool | 🟢 | bun |
| 25110 | GRAFANA_PORT | grafana | 🟢 | bun |
| 25110 | GRAFANA_PORT | grafana | 🟢 | bun |
| 25111 | — | tau | 🟢 | MainThread |
| 25112 | GHAS_API_PORT | search-api | 🟢 | bun |
| 25112 | GHAS_API_PORT | search-api | 🟢 | bun |
| 25113 | GHAS_MCP_PORT | — | 🟢 | bun |
| 25113 | GHAS_MCP_PORT | — | 🟢 | bun |
| 25114 | GHAS_FRONTEND_PORT | search-ui | ⚪️ | — |
| 25114 | GHAS_FRONTEND_PORT | search-ui | ⚪️ | — |
| 25115 | MESH_HUB_PORT | mesh-hub | 🟢 | bun |
| 25115 | MESH_HUB_PORT | mesh-hub | 🟢 | bun |
| 25116 | KIMI_AUDIT_DASH_PORT | — | 🟢 | bun |
| 25116 | KIMI_AUDIT_DASH_PORT | — | 🟢 | bun |
| 25117 | HINDSIGHT_API_PORT | hindsight | 🟢 | hindsight-api |
| 25117 | HINDSIGHT_API_PORT | hindsight | 🟢 | hindsight-api |
| 25118 | HINDSIGHT_CP_PORT | — | 🟢 | next-server (v |
| 25118 | HINDSIGHT_CP_PORT | — | 🟢 | next-server (v |
| 25120 | SOVEREIGN_CHAT_PORT | sovereign-chat | 🟢 | bun |
| 25120 | SOVEREIGN_CHAT_PORT | sovereign-chat | 🟢 | bun |
| 25121 | BYTE_VISION_PORT | byte-vision | 🟢 | python3 |
| 25121 | BYTE_VISION_PORT | byte-vision | 🟢 | python3 |
| 25122 | BEELLAMA_PORT | beellama-fast | 🟢 | llama-server |
| 25122 | BEELLAMA_PORT | beellama-fast | 🟢 | llama-server |
| 25123 | IK_LLAMA_PORT | — | ⚪️ | — |
| 25124 | TURBO_PORT | — | ⚪️ | — |
| 25125 | PI_AGENT_PORT | — | ⚪️ | — |
| 25126 | KIMI_CODE_PORT | kimi-code | 🟢 | kimi-code |
| 25126 | KIMI_CODE_PORT | kimi-code | 🟢 | kimi-code |
| 25127 | MCPPROXY_GO_PORT | gatehouse | 🟢 | gatehouse |
| 25127 | MCPPROXY_GO_PORT | gatehouse | 🟢 | gatehouse |
| 25128 | ANTIGRAVITY_GATEWAY_PORT | — | ⚪️ | — |
| 25129 | ZED_PORT | — | ⚪️ | — |
| 25130 | BROWSERLESS_PORT | browserless | 🟢 | MainThread |
| 25130 | BROWSERLESS_PORT | browserless | 🟢 | MainThread |
| 25131 | SOV_GHAS_PORT | — | ⚪️ | — |
| 25132 | SYS_MONITOR_PORT | — | ⚪️ | — |
| 25133 | QDRANT_HTTP_PORT | — | 🟢 | qdrant-server |
| 25133 | QDRANT_HTTP_PORT | — | 🟢 | qdrant-server |
| 25134 | QDRANT_GRPC_PORT | — | 🟢 | qdrant-server |
| 25134 | QDRANT_GRPC_PORT | — | 🟢 | qdrant-server |
| 25135 | SQUAWK_FEED_PORT | — | 🟢 | python3 |
| 25135 | SQUAWK_FEED_PORT | — | 🟢 | python3 |
| 25136 | ZELLIJ_PORT | fleet-ui | 🟢 | bun |
| 25136 | ZELLIJ_PORT | fleet-ui | 🟢 | bun |
| 25137 | TTYD_PORT | bedrock-ui | 🟢 | bun |
| 25137 | TTYD_PORT | bedrock-ui | 🟢 | bun |
| 25138 | SSHX_PORT | — | ⚪️ | — |
| 25139 | MISE_PORT | — | ⚪️ | — |
| 25140 | ANTIGRAVITY_CLI_PORT | — | ⚪️ | — |
| 25141 | BUN_RUNTIME_PORT | — | ⚪️ | — |
| 25142 | BUN_DEV_PORT | — | 🟢 | bun |
| 25142 | BUN_DEV_PORT | — | 🟢 | bun |
| 25143 | COYOTE_PORT | coyote | 🟢 | python3 |
| 25143 | COYOTE_PORT | coyote | 🟢 | python3 |
| 25144 | KAFKA_PORT | kafka | 🟢 | — |
| 25144 | KAFKA_PORT | kafka | 🟢 | — |
| 25145 | TAU_CODE_PORT | — | ⚪️ | — |
| 25146 | WHATSAPP_MCP_PORT | whatsapp-mcp | 🟢 | python |
| 25146 | WHATSAPP_MCP_PORT | whatsapp-mcp | 🟢 | python |
| 25147 | SQUAWK_WS_PORT | squawk-ws | 🟢 | python3 |
| 25147 | SQUAWK_WS_PORT | squawk-ws | 🟢 | python3 |
| 25148 | BRAND_PORT | flicker | 🟢 | flicker-server |
| 25148 | BRAND_PORT | flicker | 🟢 | flicker-server |
| 25149 | PAPER_POLLER_PORT | paper-poller | 🟢 | python3 |
| 25149 | PAPER_POLLER_PORT | paper-poller | 🟢 | python3 |
| 25150 | PAPER_POLLER_WATCHDOG_PORT | paper-poller-watchdog | 🟢 | python3 |
| 25150 | PAPER_POLLER_WATCHDOG_PORT | paper-poller-watchdog | 🟢 | python3 |
| 25151 | — | oracle-core | 🟢 | python3 |
| 25152 | TOOLCALL_PORT | toolcall-llm | 🟢 | llama-server |
| 25152 | TOOLCALL_PORT | toolcall-llm | 🟢 | llama-server |
| 25153 | KIMI_AUTO_SHIM_PORT | kimi-auto-shim | 🟢 | python3 |
| 25153 | KIMI_AUTO_SHIM_PORT | kimi-auto-shim | 🟢 | python3 |
| 25160 | FORENSICS_SRV_PORT | — | 🟢 | python |
| 25160 | FORENSICS_SRV_PORT | — | 🟢 | python |
| 25161 | HERD_RACE_PORT | — | ⚪️ | — |
| 25163 | NIM_KIMI_SIDECAR_PORT | nim-kimi-sidecar | 🟢 | python3 |
| 25163 | NIM_KIMI_SIDECAR_PORT | nim-kimi-sidecar | 🟢 | python3 |
| 25180 | ML_SERVE_PORT | ml-serve | 🟢 | python3 |
| 25180 | ML_SERVE_PORT | ml-serve | 🟢 | python3 |
| 25181 | BENCH_RADAR_PORT | bench-radar | 🟢 | bun |
| 25181 | BENCH_RADAR_PORT | bench-radar | 🟢 | bun |
| 25189 | NIM_QUEUE_PORT | — | ⚪️ | — |
| 25190 | REASONING_ROUTER_PORT | — | ⚪️ | — |
| 25191 | NIM_VALIDATION_PORT | — | ⚪️ | — |
| 25192 | CUTTINGGATE_PORT | — | ⚪️ | — |
| 25193 | FLOCK_PORT | flock | 🟢 | flock |
| 25193 | FLOCK_PORT | flock | 🟢 | flock |
| 25194 | RALPH_DASH_PORT | ralph-dashboard | 🟢 | uvicorn |
| 25194 | RALPH_DASH_PORT | ralph-dashboard | 🟢 | uvicorn |
| 25195 | CODEBASE_MEMORY_PORT | codebase-memory | 🟢 | codebase-memory |
| 25195 | CODEBASE_MEMORY_PORT | codebase-memory | 🟢 | codebase-memory |
| 25196 | OPENFANG_KERNEL_PORT | openfang | 🟢 | openfang |
| 25196 | OPENFANG_KERNEL_PORT | openfang | 🟢 | openfang |
| 25197 | BOUNDLESS_PORT | boundless | 🟢 | python |
| 25197 | BOUNDLESS_PORT | boundless | 🟢 | python |
| 25198 | AWR_MCP_PORT | awrawr-mcp | 🟢 | python |
| 25198 | AWR_MCP_PORT | awrawr-mcp | 🟢 | python |
| 25199 | REDIS_PORT | redis | 🟢 | valkey-server |
| 25199 | REDIS_PORT | redis | 🟢 | valkey-server |
| 25201 | RUST_WEB_BACKEND_PORT | rust-web | 🟢 | sovereign_web |
| 25201 | RUST_WEB_BACKEND_PORT | rust-web | 🟢 | sovereign_web |
| 25202 | GEMINI_MCP_PORT | — | ⚪️ | — |
| 25204 | WS_EXEC_PORT | awrawr-ws-exec | 🟢 | python |
| 25204 | WS_EXEC_PORT | awrawr-ws-exec | 🟢 | python |
| 25205 | PROMETHEUS_BACKEND_PORT | — | 🟢 | prometheus |
| 25205 | PROMETHEUS_BACKEND_PORT | — | 🟢 | prometheus |
| 25206 | HF_DOWNLOADER_BACKEND_PORT | — | 🟢 | hfdownloader |
| 25206 | HF_DOWNLOADER_BACKEND_PORT | — | 🟢 | hfdownloader |
| 25207 | MESH_LANDING_PORT | mesh-landing | 🟢 | python3 |
| 25207 | MESH_LANDING_PORT | mesh-landing | 🟢 | python3 |
| 25208 | NGINX_PORT | nginx | 🟢 | nginx |
| 25208 | NGINX_PORT | nginx | 🟢 | nginx |
| 25209 | MATTER_SERVER_PORT | matter-server | 🟢 | MainThread |
| 25209 | MATTER_SERVER_PORT | matter-server | 🟢 | MainThread |
| 25210 | GRAFANA_BACKEND_PORT | — | 🟢 | grafana |
| 25210 | GRAFANA_BACKEND_PORT | — | 🟢 | grafana |
| 25211 | NODE_EXPORTER_PORT | node-exporter | 🟢 | node_exporter |
| 25211 | NODE_EXPORTER_PORT | node-exporter | 🟢 | node_exporter |
| 25212 | COCKPIT_PORT | — | 🟢 | — |
| 25212 | COCKPIT_PORT | — | 🟢 | — |
| 25213 | — | sovereign-exporter | 🟢 | python3 |
| 25215 | — | sovereign-stream-broker | 🟢 | bun |
| 25219 | WINDMILL_PORT | windmill | 🟢 | bun |
| 25219 | WINDMILL_PORT | windmill | 🟢 | bun |
| 25220 | — | — | 🟢 | bun |
| 25240 | — | — | 🟢 | flicker-server |
| 25995 | — | — | 🟢 | bun |
| 25996 | — | — | 🟢 | bun |
| 25997 | — | — | 🟢 | bun |
| 33035 | — | — | 🟢 | — |
| 33717 | — | — | 🟢 | omp |
| 34213 | — | — | 🟢 | — |
| 34292 | — | — | 🟢 | MainThread |
| 34567 | — | files | 🟢 | python3 |
| 35017 | — | — | 🟢 | — |
| 35789 | — | — | 🟢 | — |
| 38141 | — | — | 🟢 | — |
| 39481 | — | — | 🟢 | — |
| 43000 | — | — | 🟢 | — |
| 46077 | — | — | 🟢 | — |
| 58050 | — | — | 🟢 | — |
| 58051 | — | — | 🟢 | — |
| 59818 | — | — | 🟢 | — |
| 60955 | — | — | 🟢 | — |

## Agent wiring

Config dir: `/home/toxic/.tau`

| Plugin | Source | Resolved | Exists |
|---|---|---|---|
| herd | `./estate/ranch/herd` | `/home/toxic/estate/ranch/herd` | 🟢 |
| flock | `./estate/ranch/flock` | `/home/toxic/estate/ranch/flock` | 🟢 |
| gatehouse | `./estate/ranch/barn/gatehouse` | `/home/toxic/estate/ranch/barn/gatehouse` | 🟢 |
| router | `./estate/tools/sovereign-router` | `/home/toxic/estate/tools/sovereign-router` | 🟢 |
| barn-browser | `./estate/ranch/barn/browserless` | `/home/toxic/estate/ranch/barn/browserless` | 🟢 |
| barn-gemini | `./estate/ranch/barn/gemini-mcp` | `/home/toxic/estate/ranch/barn/gemini-mcp` | 🟢 |
| secretsmith | `./projects/range/ranch/barn/secretsmith` | `/home/toxic/projects/range/ranch/barn/secretsmith` | 🟢 |

| Provider key | baseUrl |
|---|---|
| `providers.openai-compatible` | `http://127.0.0.1:25100/v1` |

- **Model-router selectors use:** `herd`, `sovereign`
- **MCP servers:** `mesh-gateway` → http://127.0.0.1:25127/mcp · `sovereign-tools` → bun /home/toxic/estate/helpers/sovereign-mcp-server.ts · `browserless` → node /home/toxic/estate/ranch/barn/browserless/dist/index.js
- **Credentials present:** flock client key: yes

## Drift

22 finding(s) — **2 high.** These are silent defects: each one is
something that looks wired and is not.

| Sev | Kind | Detail | Fix |
|---|---|---|---|
| high | `duplicate-checkout` | https://github.com/toxicwind/ranch checked out 2x — newest 6a4640f @ /home/toxic/estate/ranch; /home/toxic/ranch @ 6a4640f (2026-10-02T06:33:45-06:00) | keep /home/toxic/estate/ranch; delete or archive /home/toxic/ranch |
| high | `daemon-path-dead` | pitchfork daemon 'nats-tail' references /home/toxic/estate/ranch/squawk/nats/run-tail.sh — absent | update pitchfork.toml [daemons.nats-tail] |
| medium | `port-ssot-dead` | ports.env claims 5000 (FLEET_POWER_INTERVAL) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25123 (IK_LLAMA_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25124 (TURBO_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25125 (PI_AGENT_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25128 (ANTIGRAVITY_GATEWAY_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25129 (ZED_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25131 (SOV_GHAS_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25132 (SYS_MONITOR_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25138 (SSHX_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25139 (MISE_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25140 (ANTIGRAVITY_CLI_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25141 (BUN_RUNTIME_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25145 (TAU_CODE_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25161 (HERD_RACE_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25189 (NIM_QUEUE_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25190 (REASONING_ROUTER_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25191 (NIM_VALIDATION_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25192 (CUTTINGGATE_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25202 (GEMINI_MCP_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `selector-provider-unwired` | model-router selects 'sovereign/…' but no provider block or baseUrl in ~/.tau maps that prefix to a live port | add a 'sovereign:' provider block with a live baseUrl, or drop the selector |
