# Sovereign Control Plane (`/home/toxic/sovereign`)

> **The primary orchestration, daemon supervisor, and control plane for the Sovereign ecosystem.**

Sovereign coordinates background daemons, port allocations, environment profiles, and developer services across the system. Workspaces in `~/projects/sovereign-projects/` consume these services over standard localhost interfaces.

---

## 🚀 Quick Launch — Web UIs & Dashboards

Sovereign integrates with **Firefox Nightly** (`firefox-nightly`) on Wayland/Hyprland:

```bash
# Open all currently active/healthy Web UIs into tabs in running Firefox
mise run open-uis
# Or directly:
./scripts/open-web-uis.sh
bun run scripts/open-web-uis.ts

# List status of all Sovereign Web UIs without opening browser
mise run list-uis
bun run scripts/open-web-uis.ts --list

# Open a specific dashboard by service id
bun run scripts/open-web-uis.ts --service herd
bun run scripts/open-web-uis.ts --service mesh
bun run scripts/open-web-uis.ts --service grafana
```

---

## 🏛️ Live Service Registry & Port SSOT

All ports strictly adhere to the single source of truth in [`config/ports.env`](./config/ports.env):

| Service | Port(s) | Type | Role & Upstream Architecture |
|---|---|---|---|
| **`herd`** | `:25100` | HTTP / SSE | Inference router (llama-swap fork), model switcher, UI playground |
| **`rust-web`** | `:25101` / `:25201` | HTTP | High-performance Rust web frontend service |
| **`openfang`** | `:25103` / `:25203` | HTTP | Autonomous agent gateway & Axiom dashboard |
| **`prometheus`**| `:25105` | HTTP | Metrics collection & scrape aggregator |
| **`hf-downloader`**| `:25106` / `:25206` | HTTP | HuggingFace model downloader mesh |
| **`null-g-proxy`**| `:25107` | HTTP | Null-gateway proxy |
| **`watchdog`** | `:25108` | HTTP | Stack health watchdog & daemon recovery monitor |
| **`mcpproxy`** | `:25109` | HTTP | Local mcpproxy service |
| **`grafana`** | `:25110` / `:25210` | HTTP | Observability dashboard (anonymous admin auto-login) |
| **`ghas-api`** | `:25112` | HTTP | GitHub Advanced Security API & code scanning backend |
| **`ghas-mcp`** | `:25113` | HTTP / MCP | GHAS MCP tool endpoint |
| **`ghas-ui`** | `:25114` | HTTP | GHAS code intelligence & search frontend |
| **`mesh-hub`** | `:25115` | HTTP | Multi-feature mesh aggregator & service catalog |
| **`kimi-audit`**| `:25116` | HTTP | Kimi token audit & telemetry dashboard |
| **`hindsight`** | `:25117` / `:25118` | HTTP | Agent vector memory API (:25117) & Control Panel (:25118) |
| **`mcp-gateway`**| `:25120` | HTTP / JSON-RPC | MCP proxy gateway & aggregator router |
| **`byte-vision`**| `:25121` | HTTP | Vision inference API & mock endpoint |
| **`beellama`** | `:25122` | HTTP | Local beellama.cpp dedicated inference backend |
| **`ik-llama`** | `:25123` | HTTP | Ik-llama engine backend |
| **`kimi-code`** | `:25126` | HTTP | Kimi Code interactive web workspace |
| **`mesh`** | `:25127` | HTTP / JSON-RPC | **`mcpproxy-go` MCP federation gateway (43 active upstreams)** |
| **`zedra-host`**| `:25130` | HTTP / TCP | Zedra host daemon & collaboration bridge |
| **`sov-ghas`** | `:25131` | HTTP | Sovereign GHAS indexer |
| **`qdrant`** | `:25133` / `:25134` | HTTP / gRPC | Vector database engine for embeddings and semantic search |
| **`hal-substrate`**| `:25143` | HTTP | Autonomous agent inference engine (`hal-loop.py`) |
| **`kafka`** | `:25144` | TCP (KRaft) | Distributed event streaming broker (GraalVM / Kafka 3.9) |
| **`tau-dash`** | `:25192` | HTTP | Tau agent execution & session dashboard |
| **`redis`** | `:25199` | TCP (RESP) | Valkey in-memory key-value cache and pubsub |

---

## 👤 Modular Profile Architecture (`profiles/`)

Sovereign decouples developer workstation specifics from repository code:

- **Loader (`profiles/loader.sh`)**: Dynamically resolves `SOVEREIGN_PROFILE="${SOVEREIGN_PROFILE:-toxic}"` and sources the corresponding profile.
- **Profiles**:
  - **`profiles/toxic/env.sh`**: Personal workstation tuning for toxic:
    - CPU architecture: AMD Ryzen 7 8700F (znver4).
    - GPU acceleration: NVIDIA RTX 3090 (24GB VRAM).
    - Local inference models: `thinkingmachines/inkling` (subagent), `local-fast` (scout).
    - Compiler tuning: `CARGO_BUILD_JOBS=12` (throttled to preserve interactive latency).
  - **`profiles/default/env.sh`**: Modular template for GitHub Actions CI and external contributors without machine hardcodes.
- **Usage**:
  ```bash
  # Loads default workstation profile (toxic)
  . ~/.profile

  # Explicitly switch to generic CI profile:
  SOVEREIGN_PROFILE=default . /home/toxic/sovereign/.profile
  ```

---

## ⚡ Hardware Architecture & Compiler Optimization (Ryzen 7 8700F)

> **Build Concurrency Notice**: Cargo is configured with `jobs = 12` in `.cargo/config.toml` (target-cpu `znver4`).

- **Why 12 jobs?** The AMD Ryzen 7 8700F has 8 physical cores (16 threads) sharing a unified **16 MiB L3 cache**. When unthrottled 16-thread `rustc` bursts run alongside `sccache`, L3 cache line thrashing and memory bus contention cause desktop and shell input lag (loadavg > 24). Setting `jobs = 12` reserves 4 hardware threads for the interactive shell, editor, and system daemons while maintaining >90% compilation throughput.
- **To UNCAP to 16 threads (dedicated headless builds)**:
  ```bash
  cargo build -j 16
  ```
- **CPU Scaling Governor**: Workstation defaults to `powersave`. For maximal burst compilation performance:
  ```bash
  echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
  ```

---

## 🛡️ Pre-Commit Security & Git Hygiene

- **Fast Single-Pass Pre-Commit Hook**: Installed in `.git/hooks/pre-commit` and `.husky/pre-commit`. Evaluates staged diffs in `< 5ms` via streaming POSIX pipe.
- **Credential Protection**: Automatically rejects commits containing high-entropy tokens (`sk-`, `ghp_`, `hf_`, `eyJh`).
- **Lockfile Freezing**: Blocks accidental edits to `bun.lock` or `package-lock.json` unless `PI_ALLOW_LOCKFILE_CHANGE=1` is set.
- **Zero-Leak Boundary**: Root `.gitignore` strictly ignores `.env*` (except `!.env.example`), `.secrets*`, private keys, and runtime logs.

---

## 📡 Rapid Verification Commands

```bash
# Test primary services:
curl -sf http://127.0.0.1:25100/v1/models >/dev/null && echo "✅ :25100 Herd (LLM)"
curl -sf http://127.0.0.1:25127/health >/dev/null && echo "✅ :25127 Mesh (MCP)"
curl -sf http://127.0.0.1:25133/ >/dev/null && echo "✅ :25133 Qdrant"
valkey-cli -p 25199 ping >/dev/null && echo "✅ :25199 Redis"

# Test pre-commit hook:
/home/toxic/sovereign/.git/hooks/pre-commit
```
