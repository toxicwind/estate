# Sovereign Stack — Master Plan (2026-07-23)

## 🔴 Critical Fixes (Do First)

### 1. Stray Process Cleanup

- **Redis on 6379**: A system-level redis is binding to the default port 6379. Pitchfork-configured redis uses 25199. Need to `kill` the stray redis or `fuser -k 6379/tcp`.
- **Port 25109 conflict**: Something (likely a previous mcpproxy or Docker container) is binding to 25109 with PID 0 (kernel-level). Need to identify and clear it.
- **Grafana IPC timeout**: Grafana actually starts fine (logs show HTTP on 26110, mesh-front on 25110). Pitchfork's `ready_http` check timed out — likely the mesh-front proxy took >63s to become reachable. Increase `ready_delay` or fix the readiness check.

### 2. Port Conflict Resolution Strategy

Pitchfork uses `port` field to check availability BEFORE starting a daemon. If a non-pitchfork process occupies that port, pitchfork fails the daemon. Fix:

- Kill all stray processes: `fuser -k 6379/tcp 25109/tcp 25110/tcp`
- Verify no Docker containers are exposing sovereign ports
- Add `retry = 3` and `ready_delay` to slow-starting daemons

## 🟡 Config Alignment (mise ↔ pitchfork ↔ ports.env)

### Current State (All Correct)

| Service           | ports.env | pitchfork.toml | mise.toml          | Status |
| ----------------- | --------- | -------------- | ------------------ | ------ |
| llama-swap        | 25100     | 25100          | ✅ up/health       | ✅     |
| rust-web          | 25101     | 25101          | ❌ missing up task | ⚠️     |
| yote              | 25102     | 25102          | ❌ missing up task | ⚠️     |
| openfang          | 25103     | 25103          | ❌ missing up task | ⚠️     |
| sovereign-router  | 25104     | 25104          | ❌ missing up task | ⚠️     |
| prometheus        | 25105     | 25105          | ✅ up/health       | ✅     |
| hf-downloader     | 25106     | 25106          | ❌ missing up task | ⚠️     |
| null-g-proxy      | 25107     | 25107          | ❌ missing up task | ⚠️     |
| mcpproxy          | 25109     | 25109          | ❌ missing up task | ⚠️     |
| grafana           | 25110     | 25110          | ✅ up/health       | ✅     |
| ghas-api          | 25112     | 25112          | ❌ missing up task | ⚠️     |
| ghas-mcp          | 25113     | 25113          | ❌ missing up task | ⚠️     |
| mesh-hub          | 25115     | 25115          | ❌ missing up task | ⚠️     |
| mcp-gateway       | 25120     | 25120          | ✅ up/health       | ✅     |
| byte-vision       | 25121     | 25121          | ✅ up/health       | ✅     |
| byte-vision-proxy | 25122     | 25122          | ✅ up/health       | ✅     |
| qdrant            | 6333      | 6333           | ✅ up/health       | ✅     |
| redis             | 25199     | 25199          | ✅ up              | ✅     |
| tailscale-funnel  | —         | —              | ❌ missing         | ⚠️     |

### Actions Needed

1. Add missing `up-*` and `down-*` tasks to mise.toml for all daemons
2. Add missing health checks
3. Ensure `mise run up` and `mise run down` cover all groups

## 🟢 Rust Web Dashboard Update

### Current Services (in main.rs)

All 21 services are defined in `get_all_services()`. Need to add:

- **itvx-telemetry** (25198) — missing from service list
- **Tailscale Funnel** — missing entirely
- **Pitchfork Supervisor** — add as meta-service

### Dashboard Features Needed

1. **Clickable service cards** — each service card links to its dashboard/health endpoint
2. **Category grouping** — LLM, Core, Monitoring, MCP, Data, Mesh
3. **Real-time status** — green/yellow/red indicators with latency
4. **Model matrix** — display the AST matrix from llama-swap config
5. **Free providers panel** — show opencode, groq, cerebras, kiro, vertex status
6. **GPU metrics** — integrate nvidia-smi output
7. **Fleet benchmarks** — link to fleet results
8. **Grafana embed** — iframe for Grafana dashboards
9. **Mesh topology** — visualize service dependencies
10. **Provider API key status** — show which keys are configured (not the values)

### Static HTML Pages

- `index.html` — Main dashboard with all service cards
- `architecture.html` — System architecture diagram
- `fleet.html` — Fleet benchmarks
- `portal.html` — Service portal with clickable links

## 🔵 llama-swap Config Review

### Current Models (40+)

| Fork          | Models                       | Context   | Notes             |
| ------------- | ---------------------------- | --------- | ----------------- |
| beellama      | qwen-flash-64k/96k/128k/256k | 64K-256K  | IQ4_XS, ~9-13GB   |
| beellama      | gemma-64k/96k/128k           | 64K-128K  | Q4_K_M, ~9-13GB   |
| beellama      | exaone-4-0-1-2b (5 quants)   | 32K       | IQ4_XS-Q80, 2-5GB |
| beellama      | qwen3.5-9b variants          | 64K-256K  | DFlash, MTP       |
| beellama      | gemma4-31b-dflash            | 128K      | Q4_K_M, ~9GB      |
| turboquant    | mn-grand-64k/96k/128k        | 64K-128K  | Q4_K_M, ~20GB     |
| turboquant    | heretic-27b-128k/256k        | 128K-256K | Q5_K_XL, ~16-18GB |
| turboquant    | gemma-4-12b (4 variants)     | 128K-256K | Q4_K_M, ~16-19GB  |
| turboquant    | gemma-4-21b-moe-reap         | 128K      | Q4_K_M, ~13GB     |
| ik_llama      | heretic-ud-64k/96k           | 64K-96K   | Q5_K_XL, ~20-22GB |
| ik_turboquant | heretic variants             | 96K-256K  | Q5_K_XL           |
| qwen          | 27b-cerebellum/dflash        | 32K-96K   | Q4_K_XL, ~17-18GB |
| holo          | 35b-a3b                      | 64K       | MoE, 3B active    |

### Free Providers

| Provider | API Key Env      | Status     |
| -------- | ---------------- | ---------- |
| opencode | (no key)         | ✅ Enabled |
| groq     | GROQ_API_KEY     | ✅ Enabled |
| cerebras | CEREBRAS_API_KEY | ✅ Enabled |
| kiro     | (no key)         | ✅ Enabled |
| vertex   | GOOGLE_API_KEY   | ✅ Enabled |

### Actions Needed

1. Verify all model GGUF files exist in `/home/toxic/projects/models/`
2. Add missing models from the AST matrix
3. Update evict_costs for all models
4. Add priority tiers for model selection
5. Verify free provider endpoints are reachable

## 🟣 Provider API Keys

### Key Status

| Provider    | Env Var                   | How to Get                     | Free Tier       |
| ----------- | ------------------------- | ------------------------------ | --------------- |
| NVIDIA NIM  | NVIDIA_API_KEY            | build.nvidia.com → API Keys    | ✅ 1000 credits |
| OpenRouter  | OPENROUTER_API_KEY        | openrouter.ai/keys             | ✅ Rate-limited |
| Groq        | GROQ_API_KEY              | console.groq.com               | ✅ 30 req/min   |
| Cerebras    | CEREBRAS_API_KEY          | cloud.cerebras.ai              | ✅ Free tier    |
| Google      | GOOGLE_API_KEY            | makersuite.google.com          | ✅ Free tier    |
| Mistral     | MISTRAL_API_KEY           | docs.mistral.ai                | ✅ Free tier    |
| DeepSeek    | DEEPSEEK_API_KEY          | platform.deepseek.com          | ✅ Free tier    |
| GLM/Zhipu   | GLM_API_KEY               | open.bigmodel.cn               | ⚠️ CN phone     |
| LLM7        | LLM7_API_KEY              | llm7.io                        | ✅ Daily limits |
| LinuxDo     | LINUXDO_API_KEY           | linux.do                       | ✅ Free         |
| Context7    | CONTEXT7_API_KEY          | context7.com                   | ✅ Free         |
| HuggingFace | HF_TOKEN                  | huggingface.co/settings/tokens | ✅ Free         |
| Cloudflare  | CLOUDFLARE_GLOBAL_API_KEY | dash.cloudflare.com            | ✅ Free         |
| Sentry      | SENTRY_ACCESS_TOKEN       | sentry.io                      | ✅ Free tier    |

### Local/No-Key Services

| Service          | Port  | Notes              |
| ---------------- | ----- | ------------------ |
| llama-swap       | 25100 | Local, no key      |
| sovereign-router | 25104 | Local, no key      |
| KeylessAI        | —     | No signup needed   |
| FreeChatGPT      | —     | Community-provided |
| Scout            | 25100 | Local dummy key    |
| Prometheus       | 25105 | Local metrics      |
| Qdrant           | 6333  | Local vector DB    |

## ⚫ Zed Settings

### Profiles

| Profile          | Provider   | Model                                  | Use Case  |
| ---------------- | ---------- | -------------------------------------- | --------- |
| default          | opencode   | free/big-pickle                        | General   |
| sovereign-max    | nvidia     | thinkingmachines/inkling               | Reasoning |
| fast-free        | groq       | llama-4-scout-17b-16e-instruct         | Speed     |
| max-context-free | openrouter | nvidia/nemotron-3-ultra-550b-a55b:free | Context   |

## 📋 Port Convention (SSOT)

| Service           | Port  | Backend | Category   |
| ----------------- | ----- | ------- | ---------- |
| llama-swap        | 25100 | 26100   | LLM        |
| rust-web          | 25101 | 26101   | Core       |
| yote              | 25102 | —       | Core       |
| openfang          | 25103 | 26103   | Core       |
| sovereign-router  | 25104 | —       | Core       |
| prometheus        | 25105 | 26105   | Monitoring |
| hf-downloader     | 25106 | 26106   | LLM        |
| null-g-proxy      | 25107 | —       | Core       |
| pitchfork         | 25108 | —       | Meta       |
| mcpproxy          | 25109 | —       | MCP        |
| grafana           | 25110 | 26110   | Monitoring |
| watchdog          | 25111 | —       | Core       |
| ghas-api          | 25112 | —       | MCP        |
| ghas-mcp          | 25113 | —       | MCP        |
| ghas-frontend     | 25114 | —       | MCP        |
| mesh-hub          | 25115 | —       | Mesh       |
| mcp-gateway       | 25120 | —       | MCP        |
| byte-vision       | 25121 | —       | MCP        |
| byte-vision-proxy | 25122 | —       | MCP        |
| redis             | 25199 | —       | Data       |
| itvx-telemetry    | 25198 | —       | Data       |
| itvx-browserless  | 25130 | —       | MCP        |
| itvx-morphe       | 25140 | —       | Core       |
| qdrant            | 6333  | —       | Data       |

## 📁 Key Files

| File                           | Purpose                       |
| ------------------------------ | ----------------------------- |
| `pitchfork.toml`               | Daemon definitions and groups |
| `mise.toml`                    | Task runner and tool versions |
| `config/ports.env`             | Port SSOT                     |
| `tools/llama-swap/config.yaml` | LLM models and routing        |
| `rust_algo_web/src/main.rs`    | Dashboard backend             |
| `rust_algo_web/static/*.html`  | Dashboard frontend            |
| `stack/services/*.sh`          | Service launcher scripts      |
| `stack/lib-ports.sh`           | Port env loader               |
| `grafana/provisioning/`        | Grafana config                |
| `prometheus.yml`               | Prometheus scrape config      |
| `AGENTS.md`                    | Agent protocol                |
| `~/.config/zed/settings.json`  | Zed editor config             |
| `~/.secrets`                   | API keys                      |

## ✅ Definition of Done

1. All services start clean with `mise run up` (no port conflicts)
2. All services stop clean with `mise run down`
3. Rust-web dashboard shows all 23+ services with clickable links
4. Grafana dashboards are provisioned and accessible
5. llama-swap models load and respond
6. Free providers (opencode, groq, cerebras, kiro, vertex) are reachable
7. AGENTS.md and README.md are updated
8. PLAN.md reflects current state (this file)
9. No stray processes on sovereign ports
10. All mise tasks match pitchfork daemons 1:1
