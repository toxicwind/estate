# Sovereign

Local multi-service stack: one OpenAI-compatible LLM front door, agent kernel, Telegram bot, ops dashboard, metrics, and optional Tailscale exposure.

**Orchestration:** `mise` + `pitchfork`
**LLM front door:** llama-swap **:25100** (toxicwind fork — no vLLM)
**Ports SSOT:** `config/ports.env` (25xxx)

There is **no Caddy** and **no separate “landing” service**. Ops UI is **rust-web** only.

---

## Quick start

```bash
cd /home/toxic/sovereign
mise install
mise run up       # owned hot-reload modules
mise run health
mise run status
mise run down
```

| Surface        | URL                                   |
| -------------- | ------------------------------------- |
| Chat UI        | http://127.0.0.1:25100/ui/            |
| OpenAI API     | http://127.0.0.1:25100/v1             |
| Ops dashboard  | http://127.0.0.1:25101/               |
| Dashboard JSON | http://127.0.0.1:25101/ops/api/status |
| MCP Gateway    | http://127.0.0.1:25120/health         |

---

## What's running (`mise run up`)

| Process               | Port      | Runtime             | Role                                                                                                            |
| --------------------- | --------- | ------------------- | --------------------------------------------------------------------------------------------------------------- |
| **llama-swap**        | **25100** | Go (toxicwind fork) | Inference router + AST Matrix Go router + `/ui` + `/v1`                                                         |
| **rust-web**          | **25101** | Rust                | Ops dashboard + embedded watchdog                                                                               |
| **yote**              | 25102     | Bun                 | Telegram / status                                                                                               |
| **openfang**          | 25103     | Bun                 | Agent kernel                                                                                                    |
| **sovereign-router**  | 25104     | Bun                 | Standalone model/matrix tooling (TS, for external use)                                                          |
| **prometheus**        | 25105     | Go                  | Metrics                                                                                                         |
| **hf-downloader**     | 25106     | Bun                 | GGUF download UI                                                                                                |
| **null-g-proxy**      | 25107     | Bun                 | Extra LLM proxy                                                                                                 |
| **mcpproxy**          | 25109     | Go                  | MCP federation (43 MCPs → 1 endpoint)                                                                           |
| **grafana**           | 25110     | Go                  | Optional dashboards                                                                                             |
| **ghas-api**          | 25112     | Bun                 | GitHub Advanced Search API                                                                                      |
| **ghas-mcp**          | 25113     | Bun                 | GHAS MCP (HTTP mode, depends on ghas-api)                                                                       |
| **mesh-hub**          | 25115     | Bun                 | 20 GHAS-inspired features × every service                                                                       |
| **byte-vision**       | 25121     | Go binary           | Vision MCP (OCR / screenshot analysis)                                                                          |
| **byte-vision-proxy** | 25122     | Bun                 | **Sovereign MCP Gateway** — trust boundary + circuit breaker + sticky affinity in front of upstream MCP servers |
| **redis**             | 25199     | Redis               | Session cache, telemetry backing store                                                                          |
| **itvx-telemetry**    | 25198     | Docker              | Telemetry pipeline                                                                                              |
| **itvx-browserless**  | 25130     | Docker              | Headless browser for scraping                                                                                   |

Backends for swap: `LLAMA_START_PORT`–`LLAMA_END_PORT` = **25001–25099** (llama-server forks).

### Inference chain

```text
clients (Zed / OpenFang / Grok / IDEs)
   └─► llama-swap :25100   (toxicwind fork)
          │  internal/astmatrix/ — ELO scoring, circuit breakers, 6 strategies
          │  SQLite WAL health DB (modernc.org/sqlite)
          └─► beellama | turboquant | ik_llama | ik_turboquant  (:25001–25099)
```

### AST Matrix Go port (in llama-swap fork)

The TypeScript AST Matrix router (`tools/sovereign-router/sovereign-router-ts/router.ts`) has been ported to Go inside the llama-swap fork at `~/projects/llama-swap-main/internal/astmatrix/`. This gives llama-swap native multi-provider routing with:

- **6 strategies:** hybrid, ast_race, sticky_affinity, weighted_elo, circuit_chain, fifo_matrix
- **ELO scoring** with circuit breaker (closed/open/half)
- **SQLite WAL** health DB for request history, model health, healing events
- **7 providers:** llama-swap (local), OpenRouter, NVIDIA NIM, Groq, Cerebras, Google, Mistral
- **40+ model aliases** mapped to CODING categories

The standalone Bun `sovereign-router` at :25104 remains for external tooling use. The Go port inside llama-swap is the primary router.

### Sovereign MCP Gateway (`:25120`)

`tools/sovereign-router/sovereign-mcp-gateway/` is a trust boundary + resource allocator in front of upstream MCP servers (e.g. `byte-vision-mcp` on `:25121`). It applies the same routing theory as the LLM router:

- **Circuit breaker** per upstream (closed/half/open) — a poisoned or down upstream is quarantined so it can't burn agent turns.
- **Sticky session affinity** — `notifications/initialized` pins a session to one upstream (commitment game).
- **Provenance-tagged tool union** — `tools/list` is namespaced `<upstream>__<tool>`; `server/discover` is synthesized locally from cached handshakes.
- **502 failover** to the next healthy upstream.

Self-serve: `GET /health`, `GET /ui`. Logic is unit-tested at 100% coverage (`bun run test:gateway:cov`).

### Sovereign Monitor — Agentic Runtime Intelligence

`tools/sovereign-monitor/` provides kernel-aware, autonomous failure-recovery primitives used by the agent loop itself:

| Module                  | Coverage | Purpose                                                                                                           |
| ----------------------- | -------- | ----------------------------------------------------------------------------------------------------------------- |
| `recursive-fallback.ts` | 88%+     | Multi-level try/catch with helpers, recursive decomposition, and watchdog escalation (ReAct / Reflexion grounded) |
| `watchdog.ts`           | 100%     | Bounded agentic-loop watchdog: judge → SIGINT → SIGKILL escalation, audit trail, MCP stdio exclusion              |
| `repo-radar.ts`         | 100%     | Autonomous repo discovery via shallow GHAS queries; novelty scoring; autonomy signal detection                    |

The recursive fallback is the **default failure discipline** for every non-trivial tool call: primary → fix_syntax (coerce input) → scaffold (write helper script) → borrow_ghas (discover pattern) → retrieve_tool (shallow MCP query) → recurse (decompose + retry smaller sub-problem) → escalate (watchdog trips). Each catch block has its own nested try/catch — no single point of failure.

### Quickshell Screenshot Integration

The agent captures the user's Hyprland desktop via quickshell (ii rice) snip tool:

- `~/.config/quickshell/ii/screenshot-region.sh` — socket-free primary capture (slurp+grim), recursive multifallback, AST-aware snip routing (code/text/image via tesseract+magick)
- `~/.config/quickshell/ii/modules/common/utils/RecursiveFallback.qml` — QML singleton engine for nested fallback
- `prune-stale-sockets.sh` — cleans crashed-instance IPC dirs

Screenshot actions: `auto` (capture + classify + route to clipboard/file), `copy` (capture + clipboard only). Print Screen key triggers `ScreenSnipToggle.qml` which calls the shell script directly (no dual-instance spawning).

---

## Why no Caddy / no landing

| Removed                                          | Why                                                                                                                                                                                                                                                                                                                         |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Caddy**                                        | Path routing fought real services (`/api/*` → openfang while rust-web also needs APIs). Port docs were wrong (`:3000` vs `CADDY_PORT=25109`). **`mise run up` never started it.** Multipath proxy not needed when every service has a stable 25xxx port. Artifacts archived under `/home/toxic/data_dumps/caddy-removed-*`. |
| **landing** (`LANDING_PORT` / Bun `src/landing`) | Duplicate static server for the same files rust-web already serves. False offshoot of rust-web. Deleted; dashboard APIs live on rust-web at **`/ops/api/*`**.                                                                                                                                                               |

All public-facing services bind to `0.0.0.0` (not `127.0.0.1`) for LAN/Tailscale access. Internal mesh-front backends stay on `127.0.0.1:26xxx`. Redis on `:25199`, Qdrant on `:6333` — both `0.0.0.0`.

Access services **directly** on their ports (LAN or Tailscale MagicDNS). Optional Funnel points at **rust-web only** — see `tailscale/README.md`.

---

## Architecture (direct ports)

```text
                    ┌─ llama-swap    :25100  (/ui, /v1, /models/sse + astmatrix Go)
 clients ──────────┼─ rust-web      :25101  (/, /ops/api/*, /health)
 (local/tailnet)   ├─ openfang      :25103  (agent kernel)
                    ├─ yote          :25102  (Telegram)
                    ├─ mcpproxy      :25109  (43 MCPs federated)
                    ├─ ghas-api      :25112  (GitHub search)
                    ├─ mesh-hub      :25115  (service mesh)
                    ├─ byte-vision   :25121  (vision MCP)
                    └─ byte-vision-p :25120  (Sovereign MCP Gateway: circuit-break + sticky + discover)

 optional: Tailscale Funnel → rust-web :25101 only (not multipath)
```

Orchestration: `pitchfork.toml` (native config, no generation). `mise run up` starts the `core` group.

---

## Hot reload

| Component    | Mechanism                                                         |
| ------------ | ----------------------------------------------------------------- |
| rust-web     | `cargo watch` via `stack/services/rust-web-hot.sh`                |
| Bun services | `bun --hot` in process modules                                    |
| prometheus   | lifecycle reload wrapper (if enabled)                             |
| llama-swap   | restart: `mise run restart-llama` (binary, not rewritten in-tree) |

After editing a process module: full `mise run down && mise run up` (pitchfork reads config on start).

---

## Configuration

| Source                             | Contents                            |
| ---------------------------------- | ----------------------------------- |
| **`config/ports.env`**             | Port SSOT (loaded by mise `_.file`) |
| **`.env.local`**                   | Optional overrides / build flags    |
| **`~/.secrets`**                   | Secrets (not in git)                |
| **`tools/llama-swap/config.yaml`** | Model matrix, macros, backends      |

Never invent port numbers in app code — use env / `src/lib/ports.ts` / `stack/lib-ports.sh`. All bind addresses use `0.0.0.0` for network accessibility (see `pitchfork.toml` for `ready_http` health checks which stay `127.0.0.1`).

---

## Project layout

```text
sovereign/
├── README.md
├── AGENTS.md                 → global rules (symlink)
├── bin/llama-swap            → fork binary (symlink → projects/llama-swap-main/)
├── config/ports.env          # SSOT ports
├── mise.toml + mise/tasks/   # up / down / health / doctor / e2e
├── pitchfork.toml            # native config (no generation)
├── stack/services/*.sh       # entry shims (llama-swap.sh, rust-web-hot.sh, ...)
├── src/                      # Bun apps (services, deploy, mcp, lib)
├── rust_algo_web/            # rust-web dashboard + watchdog
├── tools/llama-swap/         # runtime binary symlink + config.yaml + MODEL_INVENTORY
├── tools/sovereign-router/         # TS sovereign-router router (standalone, port 25104)
├── tools/sovereign-monitor/        # recursive-fallback, watchdog, repo-radar (agentic runtime)
├── tests/                          # unit + integration tests (≥88% coverage enforced)
├── grafana/provisioning/  # plugins/ + alerting/ dirs (empty but required)
├── tailscale/                # optional Funnel (no Caddy)
└── backup/                   # legacy — do not stage / do not delete casually
```

---

## Zed Provider Integration

Zed is configured to connect directly to Sovereign Stack services. All provider configs live in `~/.config/zed/settings.json`.

### Sovereign Stack providers

| Provider                  | Wire                                | Port     | Why                                                                                                                 |
| ------------------------- | ----------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------- |
| **llama-swap**            | `LlamaCppLanguageModelProvider`     | `:25100` | Local GGUF inference via the toxicwind fork. Routes to beellama, turboquant, ik_llama backends on `:25001–25099`.   |
| **sovereign-router**      | Custom `sovereign-router` provider  | `:25104` | 5-strategy AST Matrix hybrid router (TS standalone). Used for external tooling.                                     |
| **Sovereign MCP Gateway** | `mcpproxy-sovereign` context server | `:25120` | Trust boundary + circuit breaker + sticky affinity in front of upstream MCP servers (e.g. byte-vision on `:25121`). |
| **mcpproxy**              | `mcpproxy-sovereign` context server | `:25109` | MCP federation (30+ MCPs → 1 endpoint). Connected via `mcp-remote` HTTP→stdio bridge.                               |

### OpenCode provider

The **OpenCode** provider (`opencode` in settings) connects to a subscription-based API gateway supporting OpenAI, Anthropic, and Google back-end routing. It auto-discovers available models via `/models` and supports `interleaved_reasoning` (thinking blocks) for multi-turn sessions. Configured with `OPENCODE_API_KEY` env var.

### Bounty providers (OpenAI-compatible)

Free/keyless endpoints configured under `language_models.openai_compatible`:

| Name            | Endpoint                         | Model                                    | Auth                 |
| --------------- | -------------------------------- | ---------------------------------------- | -------------------- |
| **Groq**        | `api.groq.com/openai/v1`         | `llama-4-scout-17b-16e-instruct`         | `GROQ_API_KEY`       |
| **OpenRouter**  | `openrouter.ai/api/v1`           | `nvidia/nemotron-3-ultra-550b-a55b:free` | `OPENROUTER_API_KEY` |
| **GLM**         | `open.bigmodel.cn/api/paas/v4`   | `glm-4.7-flash`                          | `GLM_API_KEY`        |
| **LLM7**        | `api.llm7.io/v1`                 | `default`                                | Keyless (`any`)      |
| **LinuxDo**     | `newapi.linuxdo.edu.rs/v1`       | `gpt-5-nano`                             | Pinned key           |
| **KeylessAI**   | `keylessai.thryx.workers.dev/v1` | `gpt-3.5-turbo`                          | Keyless (`any`)      |
| **FreeChatGPT** | `free.chatgpt.org/v1`            | `gpt-3.5-turbo`                          | Keyless (`any`)      |

### Custom Zed providers (in-tree)

| Provider                   | File                                                            | Why                                                                                                                                                                                |
| -------------------------- | --------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **nvidia**                 | `crates/language_models/src/provider/nvidia.rs`                 | Full JSON Schema for NVIDIA NIM (Inkling). Avoids the `JsonSchemaSubset` → vLLM 500 loop on large MCP tool sets. Supports `interleaved_reasoning` (msg-level `reasoning_content`). |
| **openai-mcpproxy**        | `crates/language_models/src/provider/openai_mcpproxy.rs`        | OpenAI-compatible endpoint fronted by mcpproxy compact router. Same schema hardening + self-healing event mapper.                                                                  |
| **openai-mcpproxy-nvidia** | `crates/language_models/src/provider/openai_mcpproxy_nvidia.rs` | Inkling through third-party OpenAI-compatible gateway (e.g. OpenRouter→Inkling). Includes **Proxy Bounty Hunter** alias.                                                           |
| **opencode**               | `crates/language_models/src/provider/opencode.rs`               | Subscription-based multi-backend gateway with auto-discover and reasoning support.                                                                                                 |

All custom providers share a **non-destructive tool-schema normalizer** (repairs missing root `type`, untyped properties, bare `null` in multi-type arrays) and a **self-healing event mapper** that turns malformed tool-call parse errors into valid `ToolUse` with `{}` input — breaking infinite retry loops on 120+ tool sets.

---

## Related forks (docs live in those repos)

| Project                | Path                                   | README focus                                                                                                       |
| ---------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| **llama-swap**         | `/home/toxic/projects/llama-swap-main` | **Fork additions**: AST Matrix Go port (`internal/astmatrix/`), `/models/sse`, `normalize_sse`, IPv4, port reclaim |
| **llama-swap runtime** | `tools/llama-swap/README.md`           | Sovereign wiring only (symlink → fork binary)                                                                      |
| **Zed**                | `/home/toxic/projects/zed`             | **toxicwind fork**: `.ignore` for agent grep, sccache+mold builds                                                  |

---

## Security

- No app auth. Treat as **localhost + Tailscale** only.
- Host firewall should drop public input; open only LAN/tailnet as you choose.
- Do not expose `:25100`/`:25101` to the open internet without your own gate.

---

## Build & Test

```bash
bun test                     # all tests (131+ tests across 9 files)
bun run test:cov             # coverage ≥88% enforced (text + lcov)
bun run test:gateway:cov     # MCP gateway core coverage (100% target)
bun run test:best-models     # model SSOT tests (live integration)
```

## Doctor / health

```bash
mise run doctor   # pitchfork + ports + hot-reload core + ast-grep pin
mise run health   # curl probes for key ports
mise run status   # pitchfork list + 25xxx listeners
```

---

## License

Stack glue: MIT where marked. Upstream binaries retain their licenses (llama-swap, Zed, Grafana, etc.).
