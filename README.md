# Sovereign

Local-first ops stack on awrawr-pc: one OpenAI-compatible LLM front door, an agent runtime, MCP federation, an ops dashboard, and metrics — orchestrated by **mise** + **pitchfork**.

## Quick start

```bash
cd /home/toxic/sovereign
mise install
mise run up        # start everything via the pitchfork supervisor
mise run health    # probe key ports
mise run status    # pitchfork list + listeners
mise run down      # stop everything
```

Service definitions are the source of truth in `pitchfork.toml` (edited directly — the old generator is retired). Port assignments live in `config/ports.env`.

## Services

### Core

| Port | Service | Role |
| ---- | ------- | ---- |
| :25100 | **herd** | OpenAI-compatible inference front door — llama-swap fork + AST Matrix router |
| :25101 | **rust-web** | Ops dashboard, `/ops/api/*` (backend on :25201) |
| :25104 | **sovereign-router** | Multi-provider LLM router (Bun/TS, 7 providers, `/ui`) |
| :25127 | **shep** | MCP federation — 30 upstream MCP servers → one endpoint |

### Agents

| Port | Service | Role |
| ---- | ------- | ---- |
| :25102 | **yote** | Telegram bot / status |
| :25103 | **axiom** | OpenFang agent host (`src/services/openfang.ts`) |
| :25143 | **coyote** | Autonomous agent inference engine — 14 providers via :25100 |
| :25125 | tau | Tau agent engine service |
| :25145 | tau-code | Tau code service |
| :25126 | kimi-code | Kimi code web UI |

### Tooling & search

| Port | Service | Role |
| ---- | ------- | ---- |
| :25106 | hf-downloader | GGUF model download UI |
| :25107 | null-g-proxy | Spare LLM proxy |
| :25112 / :25114 | search-api / search-ui | GitHub code search (GHAS) |
| :25115 | mesh-hub | Service discovery + health |
| :25116 | kimi-audit-dash | Kimi token audit dashboard |
| :25117 | hindsight | Agent memory (vectorize-io/hindsight) |
| :25120 | mcp-gateway | Sovereign MCP gateway — trust boundary + circuit breaker + sticky affinity (code at `mesh/router/sovereign-mcp-gateway/`; supervisor wiring in progress) |
| :25121 | byte-vision | Vision MCP (OCR / screenshots) |
| :25130 | itvx-browserless | Headless browser (native) |
| :25146 | whatsapp-mcp | WhatsApp Cloud API MCP |
| :25147 | squawk-ws | Squawk websocket feed |
| :8378 | gemini-mcp | Gemini API MCP |

### Data & infrastructure

| Port | Service | Role |
| ---- | ------- | ---- |
| :25105 | prometheus | Metrics |
| :25110 | grafana | Dashboards |
| :25133 | qdrant | Vector store |
| :25144 | kafka | Event bus |
| :25199 | redis | Session cache / telemetry store |
| :8000 | nim-proxy | NVIDIA NIM proxy (keyed) |
| :62200 | nginx | Local reverse proxy |
| :53 | dnsmasq | Local DNS |
| :5580 | matter-server | Matter smart-home bridge |
| :10200 | boundless | Document ingestion + chunking |

## Inference chain

```text
clients (Zed / OpenFang / IDEs)
  └─► herd :25100  (llama-swap fork + AST Matrix Go router)
        ├─► local backends :25001–:25099  (llama-server forks: beellama, turboquant, ik_llama, ik_llama-turboquant)
        └─► cloud providers via AST Matrix (openrouter, nvidia, groq, …)
```

## AST Matrix routing

Two implementations, one theory:

- **Go** (`herd/internal/astmatrix/`) — compiled into the front door. 8 strategies, 13 providers, SQLite-backed health DB with ELO scoring and circuit breakers. See `herd/README_ASTMATRIX_V2.md`.
- **TypeScript** (`tools/sovereign-router/sovereign-router-ts/router.ts`) — standalone Bun service on :25104 for external tooling. 7 providers: llama-swap, openrouter, nvidia, groq, cerebras, google, mistral.

Per-request strategy override: `X-Sovereign-Strategy: free` races local + free-tier cloud models.

## Sovereign Monitor

`tools/sovereign-monitor/` — failure-recovery primitives for the agent loop: recursive fallback (try → fix → scaffold → borrow → decompose → escalate), a bounded watchdog (judge → SIGINT → SIGKILL), and repo-radar (autonomous repo discovery).

## Configuration

| Source | Contents |
| ------ | -------- |
| `config/ports.env` | Port SSOT (loaded by mise) |
| `config/herd.yaml` | Inference routing matrix + backends |
| `~/.secrets` | Secrets (never in git) |
| `.env.local` | Optional local overrides |

Never invent port numbers in app code — read them from env, `src/lib/ports.ts`, or `stack/lib-ports.sh`.

## Project layout

```text
sovereign/
├── pitchfork.toml          # service definitions (supervisor)
├── mise.toml               # up / down / health / status / doctor tasks
├── config/                 # ports.env, herd.yaml
├── stack/services/         # service entry scripts (herd.sh, coyote.sh, …)
├── src/                    # Bun services (yote, mesh-hub, openfang, mcp, …)
├── herd/                   # llama-swap fork source + AST Matrix Go router
├── mesh/                   # MCP gateway + router variants + mesh config
├── openfang/               # placeholder — live work is in sovereign-projects
├── qed/                    # zed fork + zedra remote substrate
├── pi-conversion/          # archived grok-build → pi.dev migration
├── tools/sovereign-router/ # TS router + monitor
├── rust_algo_web/          # rust-web dashboard source
├── tailscale/              # optional Funnel exposure → rust-web :25101
└── docs/                   # deeper docs
```

## Workspaces

Application code lives in the sibling monorepo **[toxicwind/sovereign-projects](https://github.com/toxicwind/sovereign-projects)** (`/home/toxic/projects/sovereign-projects/`) — herd, mesh, tau, yote, openfang, qed, shell, boundless. This repo is the ops/control plane: services, supervisor, ports, configs.

## Zed integration

Zed talks directly to the stack (`~/.config/zed/settings.json`):

| Provider | Wire | Port |
| -------- | ---- | ---- |
| nvidia | NVIDIA NIM, direct | external |
| llama-swap | llama.cpp provider | :25100 |
| sovereign-router | OpenAI-compatible | :25104 |
| shep | MCP context server | :25127 |

Free-tier bounty aliases route through :25104 — full list in the Zed settings. Custom in-tree providers (NVIDIA schema hardening, MCP-proxy tool normalizers) live in the zed fork.

## Why no Caddy

Caddy's path routing fought real services and its port docs drifted; every service already has a stable 25xxx port, so a multipath proxy was never needed. Removed (artifacts archived). Optional public exposure is Tailscale Funnel → rust-web :25101 only — see `tailscale/`.

## Security

- No app auth. Treat as **localhost + Tailscale** only.
- Never expose :25100 / :25101 to the open internet without your own gate.

## Build & test

```bash
bun test                     # unit + integration
bun run test:cov             # coverage (≥88% enforced)
mise run doctor              # pitchfork + ports + hot-reload core
```

## License

Stack glue: MIT where marked. Upstream binaries keep their licenses (llama-swap, Zed, Grafana, …).
