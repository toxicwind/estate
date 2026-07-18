# Sovereign Control Plane

Aesthetic map of live dashboards, APIs, and MCP surfaces (25xxx SSOT).

## Dashboards

| UI | URL | Notes |
|----|-----|--------|
| Control Plane portal | http://127.0.0.1:25101/portal.html | Live service grid + API table |
| Command Center | http://127.0.0.1:25101/ | rust-web YOTE ops |
| Llama-swap chat | http://127.0.0.1:25100/ui/ | Primary chat UI |
| OpenFang | http://127.0.0.1:25103/ | Agent kernel web UI |
| Grafana | http://127.0.0.1:25110/ | Prom dashboards |
| HF Downloader | http://127.0.0.1:25106/ | GGUF fetch |
| Mesh hub | http://127.0.0.1:25115/mesh/discover | 20 features × services |

## APIs

| Surface | Base |
|---------|------|
| LLM OpenAI-compat | `:25100/v1` |
| OpenFang agents / chat | `:26103` (backend) or `:25103` (mesh-front) |
| Ops JSON | `:25101/ops/api/*` · mesh `:25101/ops/api/mesh` |
| Yote → OpenFang (HTTP only) | `:25102/api/openfang/*` |
| GHAS API / MCP HTTP | `:25112` / `:25113` |
| null-g (Bun) | `:25107` |

## MCP (Grok + Zed)

| Server | How |
|--------|-----|
| **ghas** | `ghas-mcp-stdio.sh` · HTTP health `:25113` |
| **llama-swap** | `bun run src/mcp/llama_swap.ts` |
| **ast-grep** | structural search |
| **filesystem / markitdown / prometheus / browserless** | see `~/.grok/config.toml` |

Zed: `context_servers` in `~/.config/zed/settings.json` (same commands).

## Runtime notes

- **No vLLM** — llama-swap is the only LLM front door.
- **null-g** is Bun-native (`Bun.serve` + Hono).
- **Yote** talks to OpenFang only via HTTP APIs (not shared OF process env).
- Orchestration: **mise + pitchfork** (process-compose retired).
