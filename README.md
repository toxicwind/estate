# Sovereign Control Plane (`~/sovereign/`)

> Authoritative supervisor for the Sovereign always-on stack. This repo is **not** the product source — it is the daemon registry, port map, and `mise`/`pitchfork` glue that wires every other Sovereign project together.

## What this is

The control plane is the single source of truth for the stack architecture, standardized on SSOT definitions and relative path enforcement for all daemon configurations.

| File | Role |
|---|---|
| `mise.toml` | **Generated.** `mise` tasks for stack orchestration. |
| `pitchfork.toml` | **Generated.** Process supervisor spec — one block per service. |
| `scripts/generate.ts` | The codegen entry point. Runs `generateAll()` to emit configs from the SSOTs below. |
| `src/services/registry.ts` | **SSOT.** Service definitions (name, group, command, env, readiness). |

Port assignments are defined in **`config/ports.env`** (single SSOT — every `25xxx` port used anywhere in the stack resolves through this file; never hardcode a port in code or scripts). The control plane consumes the **`sovereign-projects`** monorepo at `/home/toxic/projects/sovereign-projects/` by absolute path — the `dir = "/home/toxic/projects/sovereign-projects/..."` lines in `pitchfork.toml` point at the upstream project for each daemon.

## Layout

```
~/sovereign/
├── pitchfork.toml              GENERATED — do not hand-edit
├── mise.toml                   GENERATED — do not hand-edit
├── config/
│   └── ports.env               SSOT — every port (25xxx range)
├── src/
│   ├── services/registry.ts    SSOT — every daemon definition
│   ├── generators/             Codegen pipeline (emits pitchfork + mise)
│   └── types/                  ServiceDef / GroupDef types
├── scripts/
│   └── generate.ts             Run this after editing the SSOTs
├── stack/services/             Per-daemon launchers (*.sh) invoked by pitchfork
├── tools/                      Helper daemons (null-g-proxy, sovereign-router, Nuvio platform)
└── docs/
    ├── CONTROL_PLANE.md        Operational contract for this repo
    ├── MANIFESTO.md            Sovereign design philosophy
    └── ARCHITECTURE.md         System-wide architecture
```

## Standardized Workflow

1. Edit the SSOTs: **`config/ports.env`** for ports/env, **`src/services/registry.ts`** for daemon specs.
2. Enforce relative paths in all daemon configurations.
3. Regenerate configs:
   ```bash
   bun run scripts/generate.ts
   ```
3. Apply:
   ```bash
   mise run up          # start everything
   mise run down        # stop everything
   mise run restart     # restart everything
   ```

`pitchfork start <name>` / `stop <name>` / `restart <name>` are what `mise run up-<name>` etc. shell out to; every per-daemon task is a thin wrapper.

## Common commands

```bash
cd ~/sovereign

# Stack-wide
mise run up            # pitchfork start --all
mise run down          # pitchfork stop --all
mise run restart       # pitchfork restart --all
mise run status        # pitchfork list
mise run health        # pitchfork list (alias for status)
mise run logs          # pitchfork logs --follow
mise run svc-check     # curl every daemon's /health, /-/healthy, /api/health

# Per-daemon
mise run up-<name>       # pitchfork start <name>
mise run down-<name>     # pitchfork stop <name>
mise run restart-<name>  # pitchfork restart <name>
mise run health-<name>   # curl one daemon's health endpoint

# Raw supervisor view
pitchfork-llm list

# Watchdog + alert on degradation
mise run health-notify  # svc-check, ntfy.sh/sovereign-alerts if any daemon fails

# Build / Nuvio / test
mise run nv-build / nv-dev / nv-test / nv-package
mise run test / test-cov / test-gateway / test-models
```

## Group taxonomy

Copied verbatim from `pitchfork.toml [groups.*]`:

| Group | Daemons |
|---|---|
| `core` | `herd`, `qdrant`, `redis`, `search-api`, `mesh` |
| `main` | `qdrant`, `redis`, `kafka`, `hal-substrate`, `yote`, `search-api`, `search-ui`, `axiom`, `rust-web`, `hf-downloader`, `null-g-proxy`, `kimi-audit-dash`, `mcp-gateway`, `byte-vision`, `pi-web-dashboard`, `tau`, `kimi-code`, `mesh`, `qed`, `zedra-host`, `antigravity-cli` |
| `agents` | `axiom`, `tau`, `kimi-code`, `zedra-host`, `antigravity-cli` |
| `search` | `search-api`, `search-ui` |
| `mcp` | `mesh` |
| `monitoring` | *(empty — reserved)* |
| `all` | every daemon below |
| `sovereign-core` | full stack minus only the inference engines: `herd`, `qdrant`, `redis`, `kafka`, `hal-substrate`, `yote`, `search-api`, `search-ui`, `axiom`, `rust-web`, `hf-downloader`, `null-g-proxy`, `kimi-audit-dash`, `mcp-gateway`, `byte-vision`, `pi-web-dashboard`, `beellama-cpp`, `ik-llama-cpp`, `llama-cpp-turboquant`, `tau`, `kimi-code`, `mesh`, `qed`, `zedra-host`, `antigravity-cli` |

`all` and `sovereign-core` both contain 25 daemons (identical set today); the only difference is that the named `groups.<foo>` blocks above are subsets used by ad-hoc `pitchfork` invocations.

## Port table

Every daemon, its readiness endpoint, and the SSOT port from `config/ports.env`:

| Daemon | Port | Group(s) | Readiness |
|---|---|---|---|
| `herd` (llama-swap) | 25100 | core, all, sovereign-core | `http://127.0.0.1:25100/health` |
| `qdrant` | 25133 (http) / 25134 (grpc) | core, main, all, sovereign-core | `http://127.0.0.1:25133/` |
| `redis` (valkey) | 25199 | core, main, all, sovereign-core | `ready_port 25199` |
| `kafka` | 25144 | main, all, sovereign-core | `ready_port 25144` |
| `hal-substrate` | 25143 | main, all, sovereign-core | `http://127.0.0.1:25143/health` |
| `yote` | 25102 | main, all, sovereign-core | `http://127.0.0.1:25102/health` |
| `search-api` (GHAS) | 25112 | core, main, search, all, sovereign-core | `http://127.0.0.1:25112/health` |
| `search-ui` (GHAS frontend) | 25114 | main, search, all, sovereign-core | `http://127.0.0.1:25114/` |
| `axiom` (OpenFang) | 25103 (api 25203) | main, agents, all, sovereign-core | `http://127.0.0.1:25103/api/health` |
| `rust-web` | 25201 (backend) | main, all, sovereign-core | `http://127.0.0.1:25201/health` |
| `hf-downloader` | 25106 (backend 25206) | main, all, sovereign-core | `http://127.0.0.1:25106/api/health` |
| `null-g-proxy` | 25107 | main, all, sovereign-core | `http://127.0.0.1:25107/health` |
| `kimi-audit-dash` | 25116 | main, all, sovereign-core | `http://127.0.0.1:25116/health` |
| `mcp-gateway` (sovereign-router) | 25120 | main, all, sovereign-core | `http://127.0.0.1:25120/health` |
| `byte-vision` | 25121 | main, all, sovereign-core | `http://127.0.0.1:25121/health` |
| `pi-web-dashboard` | 25192 | main, all, sovereign-core | `http://127.0.0.1:25192/api/health` |
| `beellama-cpp` | 25122 (engine listens 25001) | all, sovereign-core | `http://127.0.0.1:25122/health` |
| `ik-llama-cpp` | 25123 (engine listens 25002) | all, sovereign-core | `http://127.0.0.1:25123/health` |
| `llama-cpp-turboquant` | 25124 (engine listens 25003) | all, sovereign-core | `http://127.0.0.1:25124/health` |
| `tau` | 25125 | main, agents, all, sovereign-core | `ready_cmd: sleep 2 && echo ready` |
| `kimi-code` | 25126 | main, agents, all, sovereign-core | `http://127.0.0.1:25126/health` |
| `mesh` (mcpproxy-go) | 25127 | core, main, mcp, all, sovereign-core | `http://127.0.0.1:25127/health` |
| `qed` (zed) | 25129 | main, all, sovereign-core | `http://127.0.0.1:25129/health` |
| `zedra-host` | 25130 | main, agents, all, sovereign-core | `http://127.0.0.1:25130/health` |
| `antigravity-cli` | 25140 | main, agents, all, sovereign-core | `http://127.0.0.1:25140/health` |

Additional SSOT ports reserved in `config/ports.env` for non-daemon services and tooling: `25101` rust-web, `25105` Prometheus, `25108` watchdog, `25109` mcpproxy legacy, `25110` Grafana, `25115` mesh-hub, `25128` antigravity-gateway, `25131` SOV_GHAS, `25132` sys-monitor, `25135` wayland-mcp, `25136` Zellij, `25137` ttyd, `25138` sshx, `25139` mise, `25141` bun-runtime, `25142` bun-dev, `25189` nim-queue, `25190` reasoning-router, `25191` nim-validation, `25203` OpenFang api, `25210` Grafana backend.

## Stack wiring

The `depends = [...]` field in `pitchfork.toml` plus runtime env references describe the actual data flow between daemons. Key edges (daemon → what it consumes):

- **`herd` (25100)** — the inference root. Everything that needs a model talks to this port. Consumed by `hal-substrate` (via `depends = ["herd"]`), `tau`, `kimi-code`, `yote`, `mesh`, `axiom`, `null-g-proxy`, `rust-web`, `mcp-gateway`, `hf-downloader`, and every C++ engine (`beellama-cpp`, `ik-llama-cpp`, `llama-cpp-turboquant`) backs models onto it.
- **`tau` (25125)** — consumes `mesh:25127` for tools (Nexus tool federation) and `herd:25100` for model inference.
- **`yote` (25102)** — Bun master agent; routes traffic through `openfang:25103` for skill dispatch and `herd:25100` for inference.
- **`mesh` (25127)** — mcpproxy-go tool federation gateway. Federates tools from upstream MCP servers into a single endpoint for `tau` and `zedra-host` to consume.
- **`axiom` / OpenFang (25103)** — agent kernel; routes to `herd:25100` for inference and offers WebChat on `:25203`.
- **`hal-substrate (25143)`** — autonomous reasoning engine. `depends = ["herd"]`. Consumes `yote:25102` and the AST Matrix hosted inside `herd`.
- **`search-api (25112)` + `search-ui (25114)`** — GHAS high-recall code search. Reads source from `mesh/search/` in `sovereign-projects`. UI is a Next.js dev server.
- **`qed (25129)` + `zedra-host (25130)`** — the editor pair: `qed` is the local Zed fork; `zedra-host` is the remote LSP host `qed` connects to.
- **`kafka (25144)`** — event bus. Wired into the `omp-kafka` OMP extension (`sovereign-events` topic). Known Java-GC permgen failure mode is documented in `docs/`.
- **`hf-downloader (25106)`** — pulls model GGUFs into `/home/toxic/projects/models/`; consumed by the three C++ engines at startup.
- **`null-g-proxy (25107)`** — tool proxy used by `null-g` extensions; bridges to upstream providers.
- **`mcp-gateway (25120)`** — sovereign-router MCP gateway. Fronts tool traffic before it reaches `mesh:25127`.
- **`rust-web (25201)`** — backend for the Sovereign dashboard and watchdog UI (port 25101 fronts it).
- **`kimi-audit-dash (25116)`** — token audit dashboard for Kimi provider.
- **`byte-vision (25121)`** — vision/OCR inference helper.
- **`pi-web-dashboard (25192)`** — prebuilt Tau web server bundle from `sovereign-projects/tau/engine/packages/server/dist/`.
- **`kimi-code (25126)`** — Kimi provider's coding-agent web UI.
- **`antigravity-cli (25140)`** — CLI helper launched from `sovereign-projects/mesh/tooling/`.

## Cross-references

- **Monorepo (source of every daemon):** [`/home/toxic/projects/sovereign-projects/`](file:///home/toxic/projects/sovereign-projects/) — see its README for per-project docs (mesh, tau, herd, qed, …).
- **`docs/CONTROL_PLANE.md`** — operational contract for this repo (what changes the SSOT, what doesn't, how regenerate/apply are gated).
- **`docs/MANIFESTO.md`** — Sovereign design philosophy (why the stack looks the way it does).
- **`docs/ARCHITECTURE.md`** — system-wide architecture (where data flows, what talks to what, why ports are 25xxx).
- **Port SSOT:** [`config/ports.env`](./config/ports.env).
- **Daemon SSOT:** [`src/services/registry.ts`](./src/services/registry.ts).
- **Codegen:** [`scripts/generate.ts`](./scripts/generate.ts) → `src/generators/index.ts`.