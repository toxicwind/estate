# Sovereign

Local multi-service stack: one OpenAI-compatible LLM front door, agent kernel, Telegram bot, ops dashboard, metrics, and optional Tailscale exposure.

**Orchestration:** `mise` + `process-compose`  
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

## What’s running (`mise run up`)

| Process | Port env | Default | Runtime | Role |
|---------|----------|---------|---------|------|
| **llama-swap** | `LLAMA_SWAP_PORT` | **25100** | Go | Inference router + `/ui` + `/v1` |
| **rust-web** | `RUST_WEB_PORT` | **25101** | Rust | Ops dashboard + embedded watchdog |
| **yote** | `YOTE_PORT` | 25102 | Bun | Telegram / status |
| **openfang** | `OPENFANG_PORT` | 25103 | Bun | Agent kernel |
| **ast-matrix** | `AST_MATRIX_PORT` | 25104 | Bun | Model/matrix tooling |
| **prometheus** | `PROMETHEUS_PORT` | 25105 | Go | Metrics (module exists; may be started outside `up` set) |
| **hf-downloader** | `HF_DOWNLOADER_PORT` | 25106 | Bun | GGUF download UI |
| **null-g-proxy** | `NULL_G_PORT` | 25107 | Bun | Extra LLM proxy |
| **process-compose** | `PROCESS_COMPOSE_PORT` | 25108 | Go | Orchestrator UI/API |
| **grafana** | `GRAFANA_PORT` | 25110 | Go | Optional dashboards |
| **watchdog** | `WATCHDOG_PORT` | 25111 | Rust (in rust-web) | Health side process |
| **ghas-api** | `GHAS_API_PORT` | 25112 | Bun | GitHub Advanced Search API |

`mise run up` starts: `llama-swap`, `openfang`, `ast-matrix`, `null-g-proxy`, `yote`, `rust-web`, `hf-downloader`, `ghas-api`.

Backends for swap: `LLAMA_START_PORT`–`LLAMA_END_PORT` = **25001–25099** (llama-server forks).

### Inference chain

```text
clients (Zed / OpenFang / Grok / IDEs)
   └─► llama-swap :25100   (toxicwind fork)
          └─► beellama | turboquant | ik_llama | ik_turboquant  (:25001–25099)
```

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
                    ┌─ llama-swap :25100  (/ui, /v1, /models/sse)
 clients ──────────┼─ rust-web  :25101  (/, /ops/api/*, /health)
 (local/tailnet)   ├─ openfang  :25103
                    ├─ yote      :25102
                    └─ … rest of config/ports.env

 optional: Tailscale Funnel → rust-web :25101 only (not multipath)
```

Orchestration: `stack/modules/*.yaml` → `process-compose.yaml` via `mise run build-compose`.

---

## Hot reload

| Component | Mechanism |
|-----------|-----------|
| rust-web | `cargo watch` via `stack/services/rust-web-hot.sh` |
| Bun services | `bun --hot` in process modules |
| prometheus | lifecycle reload wrapper (if enabled) |
| llama-swap | restart: `mise run restart-llama` (binary, not rewritten in-tree) |

After editing a process module: full `mise run down && mise run up` (process-compose does not re-read modules on process restart alone).

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
├── config/ports.env          # SSOT ports
├── mise.toml + mise/tasks/   # up / down / health / doctor / e2e
├── process-compose.yaml      # generated
├── stack/modules/*.yaml      # one process per file
├── stack/services/*.sh       # entry shims (thin)
├── src/                      # Bun apps (services, deploy, mcp, lib)
├── rust_algo_web/            # rust-web dashboard + watchdog
├── tools/llama-swap/         # runtime binary symlink + config.yaml
├── tools/ast-matrix/ …
├── grafana/provisioning/
├── tailscale/                # optional Funnel (no Caddy)
└── backup/                   # legacy — do not stage / do not delete casually
```

---

## Related forks (docs live in those repos)

| Project | Path | README focus |
|---------|------|--------------|
| **llama-swap** | `/home/toxic/projects/llama-swap-main` | **Fork additions** first (`/models/sse`, `normalize_sse`, IPv4, port reclaim) |
| **llama-swap runtime** | `tools/llama-swap/README.md` | Sovereign wiring only |
| **Zed** | `/home/toxic/projects/zed` | **toxicwind fork**: `.ignore` for agent grep, sccache+mold builds |

---

## Security

- No app auth. Treat as **localhost + Tailscale** only.
- Host firewall should drop public input; open only LAN/tailnet as you choose.
- Do not expose `:25100`/`:25101` to the open internet without your own gate.

---

## Doctor / health

```bash
mise run doctor   # modules + ast-grep pin + rust-web-hot
mise run health   # curl probes for key ports
```

---

## License

Stack glue: MIT where marked. Upstream binaries retain their licenses (llama-swap, Zed, Grafana, etc.).
