# Sovereign

Local multi-fork LLM stack on **25xxx ports**. Orchestration: **mise + process-compose**. Inference router: **llama-swap** only. **No vLLM.**

Root: `/home/toxic/sovereign`

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    mise + process-compose                │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│llama-swap│ rust-web │ openfang │   yote   │ null-g-proxy│
│  :25100  │  :25101  │  :25103  │  :25102  │    :8787    │
│  (Go)    │  (Rust)  │  (Bun)   │  (Bun)   │   (Bun)     │
└──────────┴──────────┴──────────┴──────────┴─────────────┘
     │           │          │          │           │
     └───────────┴──────────┴──────────┴───────────┘
              OpenAI-compatible /v1/* API surface
```

## Language hierarchy

| Layer | Runtime | What it owns |
|-------|---------|-------------|
| **Bun** (`src/`) | Primary | MCP, deploy, services, glue, IDE wiring, e2e tests |
| **Rust** (`rust_algo_web/`) | Hot path | Web dashboard + watchdog |
| **Go** (llama-swap) | Untouched | Inference router — do NOT rewrite |
| **Shell** | Thin only | mise task wrappers + service entry shims |

---

## Port map (SSOT: `mise.toml` `[env]`)

| Port | Service | Notes |
|------|---------|-------|
| **8787** | null-g-proxy | LLM proxy |
| **25001–25099** | llama-server backends | Spawned by llama-swap |
| **25100** | **llama-swap** | OpenAI `/v1/*` + chat UI `/ui/` |
| **25101** | rust-web | Ops dashboard + watchdog |
| **25102** | yote | Telegram bot / status |
| **25103** | openfang | Agent kernel |
| **25104** | watchdog | Embedded in rust-web |
| **25105** | prometheus | Metrics |
| **25106** | hf-downloader | Quant rank + download Web UI |

| Surface | URL |
|---------|-----|
| **Chat** | http://127.0.0.1:25100/ui/ |
| Dashboard | http://127.0.0.1:25101/ |
| API | `LLM_BASE_URL=http://127.0.0.1:25100/v1` |

---

## Quick start

```bash
cd /home/toxic/sovereign
mise install          # process-compose, python, bun, node
mise run up           # or: up-core | up-full
mise run health
mise run status
```

Stop:

```bash
mise run down
```

---

## mise tasks

| Task | Purpose |
|------|---------|
| `build-compose` | Merge `stack/modules/*.yaml` → `process-compose.yaml` |
| `up-core` | llama-swap + openfang + prometheus + null-g-proxy |
| `up` | sovereign: core + yote + rust-web |
| `up-full` | all modules + hf-downloader |
| `down` | stop process-compose |
| `health` | probe all health endpoints (core fail = exit 1) |
| `status` | process list |
| `models` | list llama-swap models on :25100 |
| `restart-llama` | reload llama-swap only |
| `restart-rust-web` | cargo release + restart dashboard |
| `test-llm` | e2e choices≥1 via MCP |

---

## Project structure

```
sovereign/
├── AGENTS.md                 # project rules
├── README.md                 # this file
├── mise.toml + mise/tasks/   # lifecycle (up/down/health)
├── process-compose.yaml      # GENERATED from stack/modules
├── package.json / bun.lock   # Bun runtime
├── .env.local                # ports, paths, flags (not secrets)
│
├── stack/
│   ├── modules/*.yaml        # process-compose process defs
│   ├── services/*.sh         # service entry shims
│   ├── build-compose.sh      # modules → process-compose.yaml
│   ├── profiles.sh           # core / sovereign / full
│   └── lib.sh                # shared helpers
│
├── src/                      # ALL app TypeScript (Bun)
│   ├── mcp/                  # MCP server + CLI e2e
│   ├── deploy/               # Insiders / IDEs / OpenFang providers
│   ├── services/             # hf-downloader, openfang, null-g-proxy
│   └── landing/              # landing server (dev only)
│
├── rust_algo_web/            # Rust web + watchdog
├── tools/llama-swap/         # config.yaml only (binary in bin/)
├── bin/                      # binaries (llama-swap, sovereign_web)
├── tests/
├── skills/
├── models -> ~/models        # GGUF runtime (not in git)
└── backup/                   # legacy history — NEVER stage
```
