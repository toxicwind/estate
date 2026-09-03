# Sovereign Control Plane

The orchestration and control layer for the Sovereign ecosystem.

## 🚀 Quick Launch — Web UIs & Dashboards

Sovereign provides first-class, standard Web UI integration with the running **Firefox Nightly** (`firefox-nightly`) instance on Wayland/Hyprland.

```bash
# Open all currently active/healthy Web UIs into tabs in running Firefox
mise run open-uis
# Or directly:
./scripts/open-web-uis.sh
bun run scripts/open-web-uis.ts

# List status of all Sovereign Web UIs without opening browser
mise run list-uis
bun run scripts/open-web-uis.ts --list

# Open all configured Web UIs (active and pending)
bun run scripts/open-web-uis.ts --all

# Open a specific dashboard by service id
bun run scripts/open-web-uis.ts --service herd
bun run scripts/open-web-uis.ts --service mesh
bun run scripts/open-web-uis.ts --service grafana
```

### Registered Web UIs & Port SSOT

All ports follow the Sovereign 25xxx SSOT in [`config/ports.env`](./config/ports.env):

| Service ID | Service Name | Port | Path | Description |
|---|---|---|---|---|
| `herd` | Herd / Llama-Swap | `:25100` | `/ui/` | Model switcher & memory monitor |
| `mesh` | MCP Mesh Gateway | `:25127` | `/` | MCP federation & active upstreams |
| `prometheus`| Prometheus | `:25105` / `:9090` | `/` | Metrics & telemetry targets |
| `grafana` | Grafana Observability | `:25110` | `/` | Anonymous admin metrics dashboard |
| `search-ui`| Seeker / GHAS Code Search | `:25114` | `/` | Code intelligence & semantic index |
| `tau-dash` | Tau Web Dashboard | `:25192` | `/` | Agent execution & session dashboard |
| `kimi-code`| Kimi Code Web IDE | `:25126` | `/` | Kimi Code interactive web workspace |
| `kimi-audit`| Kimi Token Audit | `:25116` | `/` | Token usage & rate telemetry |
| `hf-downloader`| HF Downloader | `:25106` | `/` | HuggingFace model downloader mesh |
| `rust-web` | Rust Web Frontend | `:25101` | `/` | High-performance Rust web frontend |
| `openfang` | OpenFang / Axiom | `:25103` | `/` | Autonomous agent dashboard |
| `ttyd` | TTYD Web Terminal | `:25137` | `/` | Web terminal interface |
| `qdrant` | Qdrant REST API | `:25133` | `/` | Vector engine status |

## 🌐 Browser Architecture & Port 9222 SSOT

- **Interactive Primary Browser**: `firefox-nightly` (Profile: `g304xzha.default-release`, native Wayland `MOZ_ENABLE_WAYLAND=1`).
  - Keybind: `SUPER + W` in Hyprland (`~/.config/hypr/custom/variables.lua`).
  - Default MIME handler: `firefox-nightly.desktop` for `http`, `https`, `html`, `pdf`.
- **Port 9222 (CDP Sandbox)**: Dedicated strictly to Chromium DevTools Protocol (CDP) for headless/headed WebGPU sandboxing (`sovereign/src/kataware-doki/cdp-node.ts`) and Playwright CDP scrapers (`tools/bugbounty/lib/helpers.mjs`).
  - `firefox-bidi.service` is disabled: Firefox Remote Agent implements WebDriver BiDi (not Chromium CDP) and binding the user's primary profile to a systemd service causes `parent.lock` collisions.

## 🛠️ Stack Orchestration

```bash
mise run up          # Start all Sovereign daemons via pitchfork
mise run down        # Stop all daemons
mise run status      # Check daemon status
mise run svc-check   # Health check all 25xxx ports
bun run scripts/generate.ts  # Re-sync configs from ports.env + registry
```

## 🏛️ Live Sovereign Architecture & Ports Matrix

All services listen in the `25xxx` range as defined in [`config/ports.env`](./config/ports.env).
All 12 core and active peripheral daemons are supervised by **Pitchfork** (`pitchfork.toml`):

| Service | Port(s) | Type | Health Probe | Status | Role / Architecture |
|---|---|---|---|---|---|
| `herd` | `:25100` | HTTP / SSE | `curl -sf http://127.0.0.1:25100/health` | **ONLINE** | Llama-Swap router, model orchestrator, GPU memory manager |
| `rust-web` | `:25101` (pub)<br>`:25201` (backend) | HTTP | `curl -sf http://127.0.0.1:25101/health` | **ONLINE** | High-performance Rust web frontend + `mesh-front` reverse proxy |
| `yote` | `:25102` | HTTP | `curl -sf http://127.0.0.1:25102/health` | **ONLINE** | Telegram bridge & OpenFang external service gateway |
| `hf-downloader` | `:25106` (pub)<br>`:25206` (backend) | HTTP / WS | `curl -sf http://127.0.0.1:25106/health` | **ONLINE** | Resumable Hugging Face model/dataset downloader mesh |
| `kimi-audit-dash` | `:25116` | HTTP | `curl -sf http://127.0.0.1:25116/health` | **ONLINE** | KTA token usage, quota telemetry & model comparison |
| `mcp-gateway` | `:25120` | HTTP / JSON-RPC | `curl -sf http://127.0.0.1:25120/health` | **ONLINE** | Sovereign MCP gateway, circuit breaker & sticky session router |
| `byte-vision` | `:25121` | HTTP | `curl -sf http://127.0.0.1:25121/health` | **ONLINE** | Vision inference API & mock endpoint |
| `mesh` | `:25127` | HTTP | `curl -sf http://127.0.0.1:25127/health` | **ONLINE** | `mcpproxy-go` MCP federation gateway (43 upstreams) |
| `qdrant` | `:25133` (HTTP)<br>`:25134` (gRPC) | HTTP / gRPC | `curl -sf http://127.0.0.1:25133/` | **ONLINE** | Vector database engine for semantic embeddings & search |
| `hal-substrate` | `:25143` | HTTP | `curl -sf http://127.0.0.1:25143/health` | **ONLINE** | Autonomous agent inference engine (`hal-loop.py`) |
| `kafka` | `:25144` | TCP (KRaft) | `ss -ltn 'sport = :25144'` | **ONLINE** | Distributed event streaming broker (GraalVM / Kafka 3.9) |
| `redis` | `:25199` | TCP (RESP) | `valkey-cli -p 25199 ping` | **ONLINE** | Valkey in-memory key-value cache and pubsub broker |

### Verification Commands

```bash
# Rapid probe of all core HTTP health endpoints:
for p in 25100 25101 25102 25106 25116 25120 25121 25127 25143 25201; do
  curl -sf "http://127.0.0.1:$p/health" >/dev/null && echo "✅ :$p" || echo "❌ :$p"
done

# Verify Qdrant, Redis, Kafka:
curl -sf "http://127.0.0.1:25133/" >/dev/null && echo "✅ :25133 qdrant"
valkey-cli -p 25199 ping >/dev/null && echo "✅ :25199 redis"
ss -ltn 'sport = :25144' | grep -q LISTEN && echo "✅ :25144 kafka"
```
