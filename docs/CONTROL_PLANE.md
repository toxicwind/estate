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

## Model catalog SSOT (llama-swap)

| Source | Role |
|--------|------|
| `tools/llama-swap/config.yaml` | Master list of what can run |
| `GET :25100/v1/models` | Live IDs + load status |
| `GET :25100/models/sse` | Load/unload events (Zed `llama.cpp` auto_discover contract) |

**Do not** maintain hand-written `available_models` inventories for local GGUFs in Zed/VS Code/Grok.

| Client | How it follows SSOT |
|--------|---------------------|
| **Zed** | `llama.cpp` + `auto_discover: true` → native `GET /models/sse` (no model list in settings) |
| **OpenFang** | `provider_urls.llama = http://127.0.0.1:25100/v1` only; agent model ids are request-time |
| **VS Code oaicopilot** | No native SSE; `code_insiders.ts` mirrors **live** `/v1/models` (optional `--watch` re-syncs on SSE) |
| **Antigravity / shells** | `.state/client-llm.env` exports `LLAMA_SWAP_MODELS_SSE` + base URLs |

```bash
bun run sync:ssot          # status JSON + OF + Zed guard
bun run sync:ssot:ides     # + VS Code / ide-test / antigravity env
bun run deploy:insiders -- --watch   # SSE→oaicopilot refresh loop
```

Helpers: `src/lib/llama_swap_ssot.ts`, `src/deploy/sync_clients_from_swap.ts`.
