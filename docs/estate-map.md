# Estate Map

**GENERATED FILE — do not hand-edit.** Rebuild with `bun projects/ops/bin/estate-map.ts`;
drift-check with `bun projects/ops/bin/estate-map.ts --check`.

Generated 2026-10-03T07:22:51.621Z on `awrawr-pc`. Estate root `/home/toxic/estate`.

> **One word, one referent.** `estate/` is the control-plane tree. `ranch/` is the inference
> monorepo. The agent engine config lives in `~/.tau`. Every daemon runs out of the path
> pitchfork names — check `repos[]` below before editing anything.

## Where things actually live

| Repo | Path | Remote | Head | Committed | Dirty | Checkout kind |
|---|---|---|---|---|---|---|
| 🟢 **estate** | `/home/toxic/estate` | https://github.com/toxicwind/estate.git | 4505f36bef | 2026-10-03T00:11:06 | 43 | nested |
| 🟢 **ranch** | `/home/toxic/estate/ranch` | https://github.com/toxicwind/ranch | 3c1a4a5 | 2026-10-02T23:57:58 | 1716 | nested |
| 🟢 **ranch** | `/home/toxic/ranch` | https://github.com/toxicwind/ranch | 3c1a4a5 | 2026-10-02T23:57:58 | 1716 | nested |
| 🟢 **tau-config** | `.tau` | — | — | — | 0 | none |

- **estate** (`/home/toxic/estate`) — control plane: pitchfork.toml, config/, bin/, bridge/, agents/, docs/, projects/
- **ranch** (`/home/toxic/estate/ranch`) — the inference estate monorepo: herd, flock, gatehouse, squawk, oracle, and the mesh provider catalog
- **ranch** (`/home/toxic/ranch`) — SECOND checkout of toxicwind/ranch — duplicate, not the daemon target
- **tau-config** (`.tau`) — coding-agent engine config (config.yml, models.yml, model-router.json, mcp.json)

## Live services

| Port | SSOT | Pitchfork daemon | Live | Process |
|---|---|---|---|---|
| 22 | — | — | 🟢 | — |
| 53 | — | — | 🟢 | — |
| 443 | — | — | 🟢 | — |
| 631 | — | — | 🟢 | — |
| 5000 | FLEET_POWER_INTERVAL | — | ⚪️ | — |
| 5037 | — | — | 🟢 | adb |
| 5355 | — | — | 🟢 | — |
| 5432 | — | — | 🟢 | — |
| 5900 | AGENT_DISPLAY_PORT | agent-display | ⚪️ | — |
| 5900 | AGENT_DISPLAY_PORT | agent-display | ⚪️ | — |
| 6080 | AGENT_VIEWER_PORT | agent-viewer | ⚪️ | — |
| 6080 | AGENT_VIEWER_PORT | agent-viewer | ⚪️ | — |
| 8000 | — | — | 🟢 | — |
| 8443 | — | — | 🟢 | — |
| 9223 | BROWSER_KEEPER_CDP_PORT | browser-keeper | ⚪️ | — |
| 9223 | BROWSER_KEEPER_CDP_PORT | browser-keeper | ⚪️ | — |
| 18384 | — | — | 🟢 | syncthing |
| 18789 | — | — | 🟢 | MainThread |
| 18924 | — | — | 🟢 | — |
| 20128 | VANSROUTER_PORT | vansrouter | ⚪️ | — |
| 20128 | VANSROUTER_PORT | vansrouter | ⚪️ | — |
| 22000 | — | — | 🟢 | syncthing |
| 25100 | HERD_PORT | herd | ⚪️ | — |
| 25100 | HERD_PORT | herd | ⚪️ | — |
| 25101 | MODEL_GUARD_PORT | model-guard | 🟢 | python3 |
| 25101 | MODEL_GUARD_PORT | model-guard | 🟢 | python3 |
| 25102 | YOTE_PORT | yote | ⚪️ | — |
| 25102 | YOTE_PORT | yote | ⚪️ | — |
| 25103 | OPENFANG_PORT | openfang-front | ⚪️ | — |
| 25103 | OPENFANG_PORT | openfang-front | ⚪️ | — |
| 25104 | SOVEREIGN_ROUTER_PORT | sovereign-router | 🟢 | bun |
| 25104 | SOVEREIGN_ROUTER_PORT | sovereign-router | 🟢 | bun |
| 25105 | PROMETHEUS_PORT | prometheus | ⚪️ | — |
| 25105 | PROMETHEUS_PORT | prometheus | ⚪️ | — |
| 25106 | HF_DOWNLOADER_PORT | hf-downloader | ⚪️ | — |
| 25106 | HF_DOWNLOADER_PORT | hf-downloader | ⚪️ | — |
| 25107 | NULL_G_PORT | null-g-proxy | ⚪️ | — |
| 25107 | NULL_G_PORT | null-g-proxy | ⚪️ | — |
| 25108 | WATCHDOG_PORT | — | ⚪️ | — |
| 25109 | KEYPOOL_PORT | keypool | ⚪️ | — |
| 25109 | KEYPOOL_PORT | keypool | ⚪️ | — |
| 25110 | GRAFANA_PORT | grafana | ⚪️ | — |
| 25110 | GRAFANA_PORT | grafana | ⚪️ | — |
| 25111 | TAU_CHUTE_PORT | tau | ⚪️ | — |
| 25111 | TAU_CHUTE_PORT | tau | ⚪️ | — |
| 25112 | GHAS_API_PORT | search-api | ⚪️ | — |
| 25112 | GHAS_API_PORT | search-api | ⚪️ | — |
| 25113 | GHAS_MCP_PORT | — | ⚪️ | — |
| 25114 | GHAS_FRONTEND_PORT | search-ui | ⚪️ | — |
| 25114 | GHAS_FRONTEND_PORT | search-ui | ⚪️ | — |
| 25115 | MESH_HUB_PORT | mesh-hub | ⚪️ | — |
| 25115 | MESH_HUB_PORT | mesh-hub | ⚪️ | — |
| 25116 | KIMI_AUDIT_DASH_PORT | — | ⚪️ | — |
| 25117 | HINDSIGHT_API_PORT | hindsight | ⚪️ | — |
| 25117 | HINDSIGHT_API_PORT | hindsight | ⚪️ | — |
| 25118 | HINDSIGHT_CP_PORT | — | ⚪️ | — |
| 25120 | SOVEREIGN_CHAT_PORT | sovereign-chat | ⚪️ | — |
| 25120 | SOVEREIGN_CHAT_PORT | sovereign-chat | ⚪️ | — |
| 25121 | BYTE_VISION_PORT | byte-vision | ⚪️ | — |
| 25121 | BYTE_VISION_PORT | byte-vision | ⚪️ | — |
| 25122 | BEELLAMA_PORT | beellama-fast | ⚪️ | — |
| 25122 | BEELLAMA_PORT | beellama-fast | ⚪️ | — |
| 25123 | IK_LLAMA_PORT | — | ⚪️ | — |
| 25124 | TURBO_PORT | — | ⚪️ | — |
| 25125 | PI_AGENT_PORT | — | ⚪️ | — |
| 25126 | KIMI_CODE_PORT | kimi-code | ⚪️ | — |
| 25126 | KIMI_CODE_PORT | kimi-code | ⚪️ | — |
| 25127 | MCPPROXY_GO_PORT | gatehouse | ⚪️ | — |
| 25127 | MCPPROXY_GO_PORT | gatehouse | ⚪️ | — |
| 25128 | ANTIGRAVITY_GATEWAY_PORT | — | ⚪️ | — |
| 25129 | ZED_PORT | — | ⚪️ | — |
| 25130 | BROWSERLESS_PORT | browserless | ⚪️ | — |
| 25130 | BROWSERLESS_PORT | browserless | ⚪️ | — |
| 25131 | SOV_GHAS_PORT | — | ⚪️ | — |
| 25132 | SYS_MONITOR_PORT | — | ⚪️ | — |
| 25133 | QDRANT_HTTP_PORT | — | ⚪️ | — |
| 25134 | QDRANT_GRPC_PORT | — | ⚪️ | — |
| 25135 | SQUAWK_FEED_PORT | — | ⚪️ | — |
| 25136 | FLEET_UI_PORT | — | 🟢 | bun |
| 25136 | FLEET_UI_PORT | — | 🟢 | bun |
| 25137 | BEDROCK_UI_PORT | bedrock-ui | ⚪️ | — |
| 25137 | BEDROCK_UI_PORT | bedrock-ui | ⚪️ | — |
| 25138 | SSHX_PORT | — | ⚪️ | — |
| 25139 | MISE_PORT | — | ⚪️ | — |
| 25140 | ANTIGRAVITY_CLI_PORT | — | ⚪️ | — |
| 25141 | BUN_RUNTIME_PORT | — | ⚪️ | — |
| 25142 | BUN_DEV_PORT | — | ⚪️ | — |
| 25143 | COYOTE_PORT | coyote | ⚪️ | — |
| 25143 | COYOTE_PORT | coyote | ⚪️ | — |
| 25144 | KAFKA_PORT | kafka | ⚪️ | — |
| 25144 | KAFKA_PORT | kafka | ⚪️ | — |
| 25145 | TAU_CODE_PORT | — | ⚪️ | — |
| 25146 | WHATSAPP_MCP_PORT | whatsapp-mcp | ⚪️ | — |
| 25146 | WHATSAPP_MCP_PORT | whatsapp-mcp | ⚪️ | — |
| 25147 | SQUAWK_WS_PORT | — | ⚪️ | — |
| 25148 | MBX_CACHE_PORT | mbx-cache | 🟢 | mise-cache |
| 25148 | MBX_CACHE_PORT | mbx-cache | 🟢 | mise-cache |
| 25149 | PAPER_POLLER_PORT | paper-poller | 🟢 | python3 |
| 25149 | PAPER_POLLER_PORT | paper-poller | 🟢 | python3 |
| 25150 | PAPER_POLLER_WATCHDOG_PORT | paper-poller-watchdog | 🟢 | python3 |
| 25150 | PAPER_POLLER_WATCHDOG_PORT | paper-poller-watchdog | 🟢 | python3 |
| 25151 | ORACLE_CORE_PORT | oracle-core | 🟢 | python3 |
| 25151 | ORACLE_CORE_PORT | oracle-core | 🟢 | python3 |
| 25152 | TOOLCALL_PORT | toolcall-llm | ⚪️ | — |
| 25152 | TOOLCALL_PORT | toolcall-llm | ⚪️ | — |
| 25153 | KIMI_AUTO_SHIM_PORT | kimi-auto-shim | 🟢 | python3 |
| 25153 | KIMI_AUTO_SHIM_PORT | kimi-auto-shim | 🟢 | python3 |
| 25160 | FORENSICS_SRV_PORT | — | 🟢 | python |
| 25160 | FORENSICS_SRV_PORT | — | 🟢 | python |
| 25161 | HERD_RACE_PORT | — | ⚪️ | — |
| 25163 | NIM_KIMI_SIDECAR_PORT | nim-kimi-sidecar | 🟢 | python3 |
| 25163 | NIM_KIMI_SIDECAR_PORT | nim-kimi-sidecar | 🟢 | python3 |
| 25180 | ML_SERVE_PORT | ml-serve | ⚪️ | — |
| 25180 | ML_SERVE_PORT | ml-serve | ⚪️ | — |
| 25181 | BENCH_RADAR_PORT | bench-radar | 🟢 | bun |
| 25181 | BENCH_RADAR_PORT | bench-radar | 🟢 | bun |
| 25189 | NIM_QUEUE_PORT | — | ⚪️ | — |
| 25190 | REASONING_ROUTER_PORT | — | ⚪️ | — |
| 25191 | NIM_VALIDATION_PORT | — | ⚪️ | — |
| 25192 | PI_WEB_DASHBOARD_PORT | — | ⚪️ | — |
| 25193 | FLOCK_PORT | flock | ⚪️ | — |
| 25193 | FLOCK_PORT | flock | ⚪️ | — |
| 25194 | RALPH_DASH_PORT | ralph-dashboard | 🟢 | uvicorn |
| 25194 | RALPH_DASH_PORT | ralph-dashboard | 🟢 | uvicorn |
| 25195 | CODEBASE_MEMORY_PORT | codebase-memory | 🟢 | codebase-memory |
| 25195 | CODEBASE_MEMORY_PORT | codebase-memory | 🟢 | codebase-memory |
| 25196 | OPENFANG_KERNEL_PORT | openfang | ⚪️ | — |
| 25196 | OPENFANG_KERNEL_PORT | openfang | ⚪️ | — |
| 25197 | BOUNDLESS_PORT | boundless | 🟢 | python |
| 25197 | BOUNDLESS_PORT | boundless | 🟢 | python |
| 25198 | AWR_MCP_PORT | awrawr-mcp | 🟢 | python |
| 25198 | AWR_MCP_PORT | awrawr-mcp | 🟢 | python |
| 25199 | REDIS_PORT | redis | ⚪️ | — |
| 25199 | REDIS_PORT | redis | ⚪️ | — |
| 25200 | CUTTINGGATE_PORT | — | 🟢 | bun |
| 25200 | CUTTINGGATE_PORT | — | 🟢 | bun |
| 25201 | RUST_WEB_BACKEND_PORT | fleet-feed | ⚪️ | — |
| 25201 | RUST_WEB_BACKEND_PORT | fleet-feed | ⚪️ | — |
| 25202 | GEMINI_MCP_PORT | — | ⚪️ | — |
| 25204 | WS_EXEC_PORT | awrawr-ws-exec | ⚪️ | — |
| 25204 | WS_EXEC_PORT | awrawr-ws-exec | ⚪️ | — |
| 25205 | PROMETHEUS_BACKEND_PORT | — | ⚪️ | — |
| 25206 | HF_DOWNLOADER_BACKEND_PORT | — | ⚪️ | — |
| 25207 | MESH_LANDING_PORT | mesh-landing | ⚪️ | — |
| 25207 | MESH_LANDING_PORT | mesh-landing | ⚪️ | — |
| 25208 | NGINX_PORT | nginx | ⚪️ | — |
| 25208 | NGINX_PORT | nginx | ⚪️ | — |
| 25209 | MATTER_SERVER_PORT | matter-server | ⚪️ | — |
| 25209 | MATTER_SERVER_PORT | matter-server | ⚪️ | — |
| 25210 | GRAFANA_BACKEND_PORT | — | ⚪️ | — |
| 25211 | NODE_EXPORTER_PORT | node-exporter | ⚪️ | — |
| 25211 | NODE_EXPORTER_PORT | node-exporter | ⚪️ | — |
| 25212 | COCKPIT_PORT | — | 🟢 | — |
| 25212 | COCKPIT_PORT | — | 🟢 | — |
| 25213 | SOVEREIGN_EXPORTER_PORT | sovereign-exporter | ⚪️ | — |
| 25213 | SOVEREIGN_EXPORTER_PORT | sovereign-exporter | ⚪️ | — |
| 25214 | ZEDRA_HOST_PORT | — | ⚪️ | — |
| 25215 | STREAM_BROKER_PORT | sovereign-stream-broker | ⚪️ | — |
| 25215 | STREAM_BROKER_PORT | sovereign-stream-broker | ⚪️ | — |
| 25216 | TTYD_PORT | — | ⚪️ | — |
| 25219 | WINDMILL_PORT | windmill | 🟢 | bun |
| 25219 | WINDMILL_PORT | windmill | 🟢 | bun |
| 33035 | — | — | 🟢 | — |
| 34213 | — | — | 🟢 | — |
| 34501 | — | — | 🟢 | MainThread |
| 34567 | FILES_PORT | files | ⚪️ | — |
| 34567 | FILES_PORT | files | ⚪️ | — |
| 35017 | — | — | 🟢 | — |
| 35789 | — | — | 🟢 | — |
| 38141 | — | — | 🟢 | — |
| 39481 | — | — | 🟢 | — |
| 43000 | — | — | 🟢 | — |
| 58050 | — | — | 🟢 | — |
| 58051 | — | — | 🟢 | — |
| 59818 | — | — | 🟢 | — |
| 60955 | — | — | 🟢 | — |

## Agent wiring

Config dir: `.tau`

| Plugin | Source | Resolved | Exists |
|---|---|---|---|

| Provider key | baseUrl |
|---|---|

- **Model-router selectors use:** none
- **MCP servers:** none
- **Credentials present:** flock client key: no

## Drift

35 finding(s) — **2 high.** These are silent defects: each one is
something that looks wired and is not.

| Sev | Kind | Detail | Fix |
|---|---|---|---|
| high | `duplicate-checkout` | https://github.com/toxicwind/ranch checked out 2x — newest 3c1a4a5 @ /home/toxic/estate/ranch; /home/toxic/ranch @ 3c1a4a5 (2026-10-02T23:57:58-06:00) | keep /home/toxic/estate/ranch; delete or archive /home/toxic/ranch |
| high | `daemon-path-dead` | pitchfork daemon 'bedrock-ui' references /home/toxic/projects/bedrock/web — absent | update pitchfork.toml [daemons.bedrock-ui] |
| medium | `port-ssot-dead` | ports.env claims 5000 (FLEET_POWER_INTERVAL) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25108 (WATCHDOG_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25113 (GHAS_MCP_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25116 (KIMI_AUDIT_DASH_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25118 (HINDSIGHT_CP_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25123 (IK_LLAMA_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25124 (TURBO_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25125 (PI_AGENT_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25128 (ANTIGRAVITY_GATEWAY_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25129 (ZED_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25131 (SOV_GHAS_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25132 (SYS_MONITOR_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25133 (QDRANT_HTTP_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25134 (QDRANT_GRPC_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25135 (SQUAWK_FEED_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25138 (SSHX_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25139 (MISE_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25140 (ANTIGRAVITY_CLI_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25141 (BUN_RUNTIME_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25142 (BUN_DEV_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25145 (TAU_CODE_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25147 (SQUAWK_WS_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25161 (HERD_RACE_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25189 (NIM_QUEUE_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25190 (REASONING_ROUTER_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25191 (NIM_VALIDATION_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25192 (PI_WEB_DASHBOARD_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25202 (GEMINI_MCP_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25205 (PROMETHEUS_BACKEND_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25206 (HF_DOWNLOADER_BACKEND_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25210 (GRAFANA_BACKEND_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25214 (ZEDRA_HOST_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
| medium | `port-ssot-dead` | ports.env claims 25216 (TTYD_PORT) — no listener, no pitchfork daemon claims it | start the daemon or drop the SSOT entry |
