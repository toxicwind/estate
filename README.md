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

| Surface | URL |
|---------|-----|
| Chat UI | http://127.0.0.1:25100/ui/ |
| OpenAI API | http://127.0.0.1:25100/v1 |
| Ops dashboard | http://127.0.0.1:25101/ |
| Dashboard JSON | http://127.0.0.1:25101/ops/api/status |

---

## What's running (`mise run up`)

| Process | Port | Runtime | Role |
|---------|------|---------|------|
| **llama-swap** | **25100** | Go (toxicwind fork) | Inference router + AST Matrix Go router + `/ui` + `/v1` |
| **rust-web** | **25101** | Rust | Ops dashboard + embedded watchdog |
| **yote** | 25102 | Bun | Telegram / status |
| **openfang** | 25103 | Bun | Agent kernel |
| **ast-matrix** | 25104 | Bun | Standalone model/matrix tooling (TS, for external use) |
| **prometheus** | 25105 | Go | Metrics |
| **hf-downloader** | 25106 | Bun | GGUF download UI |
| **null-g-proxy** | 25107 | Bun | Extra LLM proxy |
| **mcpproxy** | 25109 | Go | MCP federation (43 MCPs → 1 endpoint) |
| **grafana** | 25110 | Go | Optional dashboards |
| **ghas-api** | 25112 | Bun | GitHub Advanced Search API |
| **ghas-mcp** | 25113 | Bun | GHAS MCP (HTTP mode, depends on ghas-api) |
| **mesh-hub** | 25115 | Bun | 20 GHAS-inspired features × every service |
| **byte-vision** | 25121 | Go binary | Vision MCP (OCR / screenshot analysis) |
| **byte-vision-proxy** | 25120 | Python | Transparent fallback proxy for byte-vision |

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

The TypeScript AST Matrix router (`tools/ast-matrix/sovereign-ast-matrix-ts/router.ts`) has been ported to Go inside the llama-swap fork at `~/projects/llama-swap-main/internal/astmatrix/`. This gives llama-swap native multi-provider routing with:

- **6 strategies:** hybrid, ast_race, sticky_affinity, weighted_elo, circuit_chain, fifo_matrix
- **ELO scoring** with circuit breaker (closed/open/half)
- **SQLite WAL** health DB for request history, model health, healing events
- **7 providers:** llama-swap (local), OpenRouter, NVIDIA NIM, Groq, Cerebras, Google, Mistral
- **40+ model aliases** mapped to CODING categories

The standalone Bun `ast-matrix` at :25104 remains for external tooling use. The Go port inside llama-swap is the primary router.

---

## Why no Caddy / no landing

| Removed | Why |
|---------|-----|
| **Caddy** | Path routing fought real services (`/api/*` → openfang while rust-web also needs APIs). Port docs were wrong (`:3000` vs `CADDY_PORT=25109`). **`mise run up` never started it.** Multipath proxy not needed when every service has a stable 25xxx port. Artifacts archived under `/home/toxic/data_dumps/caddy-removed-*`. |
| **landing** (`LANDING_PORT` / Bun `src/landing`) | Duplicate static server for the same files rust-web already serves. False offshoot of rust-web. Deleted; dashboard APIs live on rust-web at **`/ops/api/*`**. |

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
                    └─ byte-vision-p :25120  (vision proxy fallback)

 optional: Tailscale Funnel → rust-web :25101 only (not multipath)
```

Orchestration: `pitchfork.toml` (native config, no generation). `mise run up` starts the `core` group.

---

## Hot reload

| Component | Mechanism |
|-----------|-----------|
| rust-web | `cargo watch` via `stack/services/rust-web-hot.sh` |
| Bun services | `bun --hot` in process modules |
| prometheus | lifecycle reload wrapper (if enabled) |
| llama-swap | restart: `mise run restart-llama` (binary, not rewritten in-tree) |

After editing a process module: full `mise run down && mise run up` (pitchfork reads config on start).

---

## Configuration

| Source | Contents |
|--------|----------|
| **`config/ports.env`** | Port SSOT (loaded by mise `_.file`) |
| **`.env.local`** | Optional overrides / build flags |
| **`~/.secrets`** | Secrets (not in git) |
| **`tools/llama-swap/config.yaml`** | Model matrix, macros, backends |

Never invent port numbers in app code — use env / `src/lib/ports.ts` / `stack/lib-ports.sh`.

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
├── tools/ast-matrix/         # TS ast-matrix router (standalone, port 25104)
├── grafana/provisioning/
├── tailscale/                # optional Funnel (no Caddy)
└── backup/                   # legacy — do not stage / do not delete casually
```

---

## Related forks (docs live in those repos)

| Project | Path | README focus |
|---------|------|--------------|
| **llama-swap** | `/home/toxic/projects/llama-swap-main` | **Fork additions**: AST Matrix Go port (`internal/astmatrix/`), `/models/sse`, `normalize_sse`, IPv4, port reclaim |
| **llama-swap runtime** | `tools/llama-swap/README.md` | Sovereign wiring only (symlink → fork binary) |
| **Zed** | `/home/toxic/projects/zed` | **toxicwind fork**: `.ignore` for agent grep, sccache+mold builds |

---

## Security

- No app auth. Treat as **localhost + Tailscale** only.
- Host firewall should drop public input; open only LAN/tailnet as you choose.
- Do not expose `:25100`/`:25101` to the open internet without your own gate.

---

## Doctor / health

```bash
mise run doctor   # pitchfork + ports + hot-reload core + ast-grep pin
mise run health   # curl probes for key ports
mise run status   # pitchfork list + 25xxx listeners
```

---

## License

Stack glue: MIT where marked. Upstream binaries retain their licenses (llama-swap, Zed, Grafana, etc.).
