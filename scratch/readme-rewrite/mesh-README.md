# Sovereign Mesh — Tool Federation Gateway & AST Matrix

**Role:** federated tool routing, AST matrix code navigation, MCP client aggregation, and multi-provider LLM routing.

| Port      | Service                                                              |
| --------- | -------------------------------------------------------------------- |
| `:25127`  | shep — MCPProxy (Go) gateway, 40+ upstream MCP servers               |
| `:25115`  | Mesh Hub — service discovery and health                              |
| `:25100`  | llama-swap — local model inference (herd)                            |
| `:25104`  | Sovereign Router TS — multi-provider LLM routing (Bun/TS + `/ui`)    |

---

## Topology

```text
mesh/
├── gateway/          ← shep — MCPProxy Go gateway (mcpproxy-go), MCP client aggregation (:25127)
├── router/           ← Sovereign Router — multi-provider LLM routing gateway
│   ├── sovereign-router-ts/      # LIVE ROUTER (Bun/TS, :25104)
│   ├── sovereign-ast-matrix-py/  # v2 Python router (FastAPI)
│   ├── sovereign-ast-router/     # v3 TS variant
│   ├── sovereign-mcp-gateway/    # MCP gateway service
│   ├── free_zed_gateway/         # free-LLM-gateway concept
│   └── bin/                      # compiled binaries
├── ast-matrix/       ← AST Matrix code extraction and semantic matrix packages
├── ui-svelte/        ← Svelte dashboard for router/llama-swap UI
├── config.yml        ← Unified mesh configuration, model roles, port mappings
├── research/         ← Research artifacts (provider discovery scripts, agent-infra dumps)
└── data/             ← JSON data dumps (model catalogs, package tables, scaffolds)
```

---

## Ports & Services

| Port     | Service                        | Description                                              |
| -------- | ------------------------------ | -------------------------------------------------------- |
| `:25127` | shep — MCPProxy (Go)           | MCP client aggregation gateway, 40+ upstream servers     |
| `:25115` | Mesh Hub                       | Mesh service discovery and health                        |
| `:25100` | llama-swap                     | Local model inference (herd config)                      |
| `:25104` | Sovereign Router TS            | Multi-provider LLM routing (Bun/TS + `/ui` dashboard)    |
| `:25103` | OpenFang                       | External LLM service proxy                               |
| `:25105` | Prometheus                     | Metrics scraping                                         |
| `:25106` | hf-downloader                  | HuggingFace model downloader                             |
| `:25110` | Grafana                        | Dashboard                                                |
| `:25114` | next-server                    | sovereign-github-search frontend                         |

---

## Model Roles

Live values from `config.yml` — mesh configures model routing per role:

| Role      | Model                                          | Purpose              |
| --------- | ---------------------------------------------- | -------------------- |
| `default` | `openrouter/inclusionai/ling-3.0-flash-fin:free:high` | Default routing model |
| `task`    | `qwen/qwen3.6-35b-a3b:high`                    | Task-oriented routing |
| `slow`    | `qwen/qwen3.6-35b-a3b:high`                    | Slow/fallback routing |
| `plan`    | `qwen/qwen3.6-35b-a3b:high`                    | Planning mode        |
| `smol`    | `qwen/qwen3.6-27b:high`                        | Small/smol routing   |
| `tiny`    | `qwen/qwen3.6-27b:high`                        | Tiny model routing   |

The `free` strategy races local llama-swap + every `:free` cloud model.

---

## Router Strategies

Set strategy per-request: `X-Sovereign-Strategy: free`

| Strategy          | Behavior                                              |
| ----------------- | ----------------------------------------------------- |
| `hybrid` (default)| sticky → ast_race → circuit_chain                     |
| `free`            | Races local llama-swap + every `:free` cloud model (zero-cost) |
| `ast_race`        | Parallel N providers, first AST/code-shaped response wins |
| `sticky_affinity` | 30-min session pinning for multi-turn                 |
| `weighted_elo`    | Dynamic Elo from success/latency                      |
| `circuit_chain`   | Sequential with open/half-open circuit breakers       |
| `fifo_matrix`     | Bounded FIFO queue (back-pressure)                    |

---

## Relationship to Herd

Herd owns the local inference layer (`llama-swap`, port `:25100`). Mesh owns the routing and gateway layer. Config connects them:

```yaml
openai-compatible:
    baseUrl: http://127.0.0.1:25100/v1
apiKey: <redacted>
```

The `ui-svelte/` dashboard is served by the router's built-in `/ui` page.

---

## Quick Verification

```bash
curl -sf http://127.0.0.1:25115/health      # mesh-hub
curl -sf http://127.0.0.1:25127/health      # MCP gateway
curl -sf http://127.0.0.1:25104/health      # sovereign router
curl -sf http://127.0.0.1:25100/v1/models   # llama-swap
```
