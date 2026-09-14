# Sovereign

Local multi-service stack: one OpenAI-compatible LLM front door, agent kernel, Telegram bot, ops dashboard, metrics, and optional Tailscale exposure.

**Orchestration:** `mise` + `pitchfork` (`pitchfork.toml` is GENERATED from `config/ports.env` — do not edit directly)
**LLM front door:** herd / llama-swap **:25100** (toxicwind fork)
**Ports SSOT:** `config/ports.env` (25xxx)

There is **no Caddy** and **no separate “landing” service**. Ops UI is **rust-web** only.

---

## Quick start

```bash
cd /home/toxic/sovereign
mise install
mise run up       # core group: herd, qdrant, redis, dnsmasq, search-api, mesh-hub, prometheus, grafana, mesh
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
| OpenFang UI    | http://127.0.0.1:25103/               |
| OpenFang API   | http://127.0.0.1:25203/               |
| Coyote         | http://127.0.0.1:25143/health         |
| HF Downloader  | http://127.0.0.1:25106/               |
| Grafana        | http://127.0.0.1:25110/               |
| MCP Gateway    | http://127.0.0.1:25120/health         |
| Mesh Hub       | http://127.0.0.1:25115/               |

---

## What's running

`mise run up` starts the **core** group (`pitchfork start --group core`):

| Process      | Port    | Runtime       | Role                                              |
| ------------ | ------- | ------------- | ------------------------------------------------- |
| **herd**     | **25100** | Go binary   | llama-swap (toxicwind fork): inference router + `/ui` + `/v1`. Binds `0.0.0.0` |
| **qdrant**   | 25133   | qdrant-server | Vector DB                                         |
| **redis**    | 25199   | valkey-server | Session cache, telemetry backing store. Binds `0.0.0.0` |
| **dnsmasq**  | —       | dnsmasq       | Local DNS (tau MCP infra)                         |
| **search-api** | 25112 | Bun           | GitHub search API (ghas-api)                      |
| **mesh-hub** | 25115   | Bun           | Service mesh features                             |
| **prometheus** | 25105 | Bash          | Metrics                                           |
| **grafana**  | 25110   | Bash          | Dashboards                                        |
| **mesh**     | **25127** | Go binary   | mcpproxy-go: MCP federation (30 MCPs → 1 endpoint). Listens `127.0.0.1` |

### Other pitchfork daemons

`pitchfork start --group <name>`. Groups: `main`, `agents` (axiom, tau, tau-code, kimi-code), `search` (search-api, search-ui), `mcp` (mcp-gateway, mesh), `monitoring` (prometheus, grafana), `all`. `nginx` is a pitchfork daemon in no group — start it explicitly.

| Daemon             | Port  | Role                                                                                          |
| ------------------ | ----- | --------------------------------------------------------------------------------------------- |
| **kafka**          | 25144 | Event bus (tau MCP infra)                                                                     |
| **coyote**         | **25143** | Autonomous agent inference engine (renamed from hal-substrate 2026-09-14; `hal-substrate.sh` is a compat shim) |
| **yote**           | 25102 | Telegram / status                                                                             |
| **search-ui**      | 25114 | GitHub search frontend (Next.js)                                                              |
| **axiom** (openfang) | **25103** | OpenFang OS agent kernel — Bun launcher (`src/services/openfang.ts`) → Rust binary, API `:25203` |
| **rust-web**       | 25101 | Ops dashboard + embedded watchdog (backend `:25201`)                                          |
| **hf-downloader**  | 25106 | GGUF download UI                                                                              |
| **null-g-proxy**   | 25107 | Extra LLM proxy                                                                               |
| **kimi-audit-dash**| 25116 | Kimi token audit dashboard (code lives outside this repo)                                     |
| **mcp-gateway**    | **25120** | Sovereign MCP Gateway — trust boundary + circuit breaker + sticky affinity in front of upstream MCP servers |
| **byte-vision**    | 25121 | Vision MCP (OCR / screenshot analysis)                                                        |
| **hindsight**      | 25117 | See `stack/services/hindsight.sh`                                                             |
| **tau**            | 25125 | Tau coding agent                                                                              |
| **tau-code**       | **25145** | Tau code service (note: `config/ports.env` still says `25144` — drift; `25144` is kafka) |
| **kimi-code**      | **25126** | kimi-code web UI (`bun run dist/main.mjs web`)                                            |
| **nginx**          | 62200 | Reverse proxy (`/etc/nginx/nginx.conf`, outside repo)                                         |

Backends for swap: **beellama `:25122`** · **ik_llama `:25123`** · **turbo `:25124`** (llama-server forks; `BEELLAMA_PORT`/`IK_LLAMA_PORT`/`TURBO_PORT` in `config/ports.env`).

### Llama-swap interfaces

| Interface             | File                    | What it is                                                                                                  |
| --------------------- | ----------------------- | ----------------------------------------------------------------------------------------------------------- |
| **herd launcher**     | `stack/services/herd.sh` | Primary pitchfork entry — launches the toxicwind fork binary (`~/projects/sovereign-projects/sovereign-swap/build/llama-swap`), config `config/herd.yaml` (fallback `config/llama-swap.yaml`), binds `0.0.0.0:25100`. |
| **MCP stdio wrapper** | `src/mcp/llama_swap.ts` | Bun MCP server (`StdioServerTransport`). Env-only config (no file reads). Used by MCP federation / gateway. |

---

### Inference chain

```text
clients (OpenFang / IDEs / agents)
   └─► herd / llama-swap :25100   (toxicwind fork, config/herd.yaml)
          └─► beellama :25122 | ik_llama :25123 | turbo :25124
```

The standalone TypeScript AST router (`tools/sovereign-router/sovereign-router-ts/router.ts`) implements 5 strategies (`fifo_matrix`, `ast_race`, `sticky_affinity`, `weighted_elo`, `circuit_chain`). It is **not** started by pitchfork — there is no `:25104` listener.

### Sovereign MCP Gateway (`:25120`)

`mesh/router/sovereign-mcp-gateway/` is a trust boundary + resource allocator in front of upstream MCP servers (e.g. `byte-vision` on `:25121`). It applies the same routing theory as the LLM router:

- **Circuit breaker** per upstream (closed/half/open) — a poisoned or down upstream is quarantined so it can't burn agent turns.
- **Sticky session affinity** — `notifications/initialized` pins a session to one upstream (commitment game).
- **Provenance-tagged tool union** — `tools/list` is namespaced `<upstream>__<tool>`; `server/discover` is synthesized locally from cached handshakes.
- **502 failover** to the next healthy upstream.

Core logic is unit-tested at 100% coverage — `bun run test:gateway:cov` (46 tests, verified 2026-09-14). Self-serve: `GET /health`.

### Sovereign Monitor — Agentic Runtime Intelligence

`tools/sovereign-monitor/` provides kernel-aware, autonomous failure-recovery primitives used by the agent loop itself (coverage re-verified 2026-09-14):

| Module                  | Coverage | Purpose                                                                                                           |
| ----------------------- | -------- | ----------------------------------------------------------------------------------------------------------------- |
| `recursive-fallback.ts` | 88%+     | Multi-level try/catch with helpers, recursive decomposition, and watchdog escalation (ReAct / Reflexion grounded) |
| `watchdog.ts`           | 100%     | Bounded agentic-loop watchdog: judge → SIGINT → SIGKILL escalation, audit trail, MCP stdio exclusion              |
| `repo-radar.ts`         | 100%     | Autonomous repo discovery via shallow GHAS queries; novelty scoring; autonomy signal detection                    |

The recursive fallback is the **default failure discipline** for every non-trivial tool call: primary → fix_syntax (coerce input) → scaffold (write helper script) → borrow_ghas (discover pattern) → retrieve_tool (shallow MCP query) → recurse (decompose + retry smaller sub-problem) → escalate (watchdog trips). Each catch block has its own nested try/catch — no single point of failure.

---

## Why no Caddy / no landing

| Removed                                          | Why                                                                                                                                                                                                                                                                                                                      |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Caddy**                                        | Path routing fought real services (`/api/*` → openfang while rust-web also needs APIs). **`mise run up` never started it.** Multipath proxy not needed when every service has a stable 25xxx port. Artifacts archived under `/home/toxic/archive/caddy-removed-*`. |
| **landing** (`LANDING_PORT` / Bun `src/landing`) | Duplicate static server for the same files rust-web already serves. False offshoot of rust-web. Deleted; dashboard APIs live on rust-web at **`/ops/api/*`**.                                                                                                                                                            |

Most services bind **`127.0.0.1`** (pitchfork `ready_http` checks). Exceptions: **herd** binds `0.0.0.0:25100`, **redis** (valkey) binds `0.0.0.0:25199`. Reach services over Tailscale to the host. **nginx `:62200`** (pitchfork daemon, not in any start group) is available as a reverse proxy. Optional Funnel points at **rust-web** only — see `tailscale/README.md`.

---

## Architecture (direct ports)

```text
                    ┌─ herd/llama-swap :25100  (/ui, /v1 — binds 0.0.0.0)
 clients ──────────┼─ rust-web      :25101  (/, /ops/api/*, /health)
 (tailnet)         ├─ openfang      :25103  (agent kernel)
                    ├─ yote          :25102  (Telegram)
                    ├─ coyote        :25143  (agent inference engine)
                    ├─ mesh          :25127  (30 MCPs federated)
                    ├─ search-api    :25112  (GitHub search)
                    ├─ mesh-hub      :25115  (service mesh)
                    ├─ byte-vision   :25121  (vision MCP)
                    └─ mcp-gateway   :25120  (circuit-break + sticky + discover)

 core group (mise run up): herd qdrant redis dnsmasq search-api mesh-hub prometheus grafana mesh
 full stack: pitchfork start --group all
 optional: Tailscale Funnel → rust-web :25101 only
```

---

## Workspaces (`toxicwind/sovereign-projects`)

The **Sovereign Workspaces** repo is the unified workspace layer that operates in tandem with this control plane.

- **GitHub**: [toxicwind/sovereign-projects](https://github.com/toxicwind/sovereign-projects)
- **Local**: `/home/toxic/projects/sovereign-projects/`
- **Subfolders**: `herd`, `mesh`, `tau`, `yote`, `openfang`, `qed`, `shell`, `packages`

| Workspace | Directory | Role | Port |
|-----------|-----------|------|------|
| **Herd** | `herd/` | Inference router & llama-swap | `:25100` |
| **Mesh** | `mesh/` | MCP federation gateway | `:25127` |
| **Tau** | `tau/` | Canonical AI coding agent engine | `:25192` |
| **Yote** | `yote/` | Minimal embeddable agent runtime | `:25102` |
| **OpenFang** | `openfang/` | Rust Agent OS | `:25103` |
| **Shell** | `shell/` | Desktop environment | Wayland |

```bash
# Clone the workspaces
git clone https://github.com/toxicwind/sovereign-projects.git /home/toxic/projects/sovereign-projects
```

Orchestration: `pitchfork.toml` (generated from `config/ports.env` — do not edit directly). `mise run up` starts the `core` group.

---

## Hot reload

| Component    | Mechanism                                                         |
| ------------ | ----------------------------------------------------------------- |
| rust-web     | `cargo watch` via `stack/services/rust-web-hot.sh`                |
| Bun services | `bun --hot` in process modules                                    |
| prometheus   | lifecycle reload wrapper (if enabled)                             |
| herd         | restart: `mise run restart-llama` (binary, not rewritten in-tree) |

After editing a process module: full `mise run down && mise run up` (pitchfork reads config on start).

---

## Configuration

| Source                  | Contents                                         |
| ----------------------- | ------------------------------------------------ |
| **`config/ports.env`**  | Port SSOT (loaded by mise `_.file`)              |
| **`config/herd.yaml`**  | herd model matrix (preferred by `herd.sh`)       |
| **`config/llama-swap.yaml`** | herd model matrix (fallback)                |
| **`.env.local`**        | Optional overrides / build flags                 |
| **`~/.secrets`**        | Secrets (not in git)                             |

Never invent port numbers in app code — use env / `src/lib/ports.ts` / `stack/lib-ports.sh`. Services bind `127.0.0.1` unless noted (herd and redis bind `0.0.0.0`); `ready_http` health checks stay `127.0.0.1`.

---

## Project layout

```text
sovereign/
├── README.md
├── AGENTS.md                          # global rules
├── config/ports.env                   # port SSOT
├── config/herd.yaml                   # herd model matrix (llama-swap.yaml fallback)
├── mise.toml + mise/tasks/            # up / down / health / status / doctor
├── pitchfork.toml                     # GENERATED from config/ports.env (do not edit)
├── stack/services/*.sh                # entry shims (herd.sh, coyote.sh, openfang.sh, ...)
├── src/                               # Bun services (services/, mcp/, lib/, ...)
├── rust_algo_web/                     # rust-web dashboard + watchdog
├── mesh/router/sovereign-mcp-gateway/ # MCP gateway (gateway.ts, 100% covered core)
├── tools/sovereign-router/           # TS AST router (standalone; not pitchfork-started)
├── tools/sovereign-monitor/          # recursive-fallback, watchdog, repo-radar
├── packages/                          # sovereign-scripts, sovereign-skills, utils
├── openfang/README.md                 # OpenFang = RightNow-AI Rust Agent OS
├── tests/                             # 8 test files (bun test runs tests/open_web_uis.test.ts)
├── grafana/provisioning/{dashboards,datasources}/
└── tailscale/                         # optional Funnel (no Caddy)
```

---

## Related forks (docs live in those repos)

| Project        | Path                                                   | README focus                                                              |
| -------------- | ------------------------------------------------------ | ------------------------------------------------------------------------- |
| **llama-swap** | `/home/toxic/projects/sovereign-projects/sovereign-swap` | toxicwind fork — `build/llama-swap` binary run by `stack/services/herd.sh` |

---

## Security

- No app auth. Treat as **localhost + Tailscale** only.
- Host firewall should drop public input; open only LAN/tailnet as you choose.
- Do not expose `:25100`/`:25101` to the open internet without your own gate.

---

## Build & Test

```bash
bun test                     # package.json: runs tests/open_web_uis.test.ts (8 test files in tests/)
bun run test:cov             # coverage report (text + lcov)
bun run test:gateway:cov     # MCP gateway core: 100% coverage (46 tests)
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

