# Mesh — Tool Federation & Routing Layer

`mesh/` holds the tool-federation and routing components: the MCP gateway source, the sovereign-router variants, AST code-navigation packages, and the unified mesh config.

## Layout

```text
mesh/
├── gateway/                    # vendored mcpproxy-go source — the engine behind shep
├── router/
│   ├── sovereign-router-ts/    # live TS router (Bun, :25104, /ui) — 7 providers
│   ├── sovereign-mcp-gateway/  # Sovereign MCP gateway source (trust boundary + circuit breaker + sticky affinity)
│   ├── sovereign-ast-matrix-py/# Python FastAPI router (v2)
│   ├── sovereign-ast-router/   # TS router variant (v3)
│   └── free_zed_gateway/       # free-LLM gateway concept
├── ast-matrix/                 # AST code extraction / semantic matrix packages
├── ui-svelte/                  # Svelte dashboard for the router
├── config.yml                  # unified mesh config — model roles, port mappings
└── research/ data/              # provider discovery scripts, model catalog dumps
```

## shep — MCP federation (:25127)

**shep** (renamed from mcpproxy) serves one endpoint in front of **30 upstream MCP servers**: quarantine for new servers, BM25 tool discovery, health checks, and security scanning. Live config: `sovereign-projects/mesh/gateway/mcp_config.json` (pitchfork `shep` daemon). Gateway source is vendored here at `gateway/` (upstream: smart-mcp-proxy/mcpproxy-go).

## sovereign-router (:25104)

The TypeScript router is the live multi-provider gateway: 7 providers (llama-swap, openrouter, nvidia, groq, cerebras, google, mistral), 5-strategy hybrid routing, built-in `/ui` dashboard. Override per request:

```bash
curl -H "X-Sovereign-Strategy: free" http://127.0.0.1:25104/v1/chat/completions
```

| Strategy | Behavior |
| -------- | -------- |
| `hybrid` (default) | sticky → ast_race → circuit_chain |
| `free` | races local llama-swap + every `:free` cloud model (zero-cost) |
| `ast_race` | parallel fan-out, first valid response wins |
| `sticky_affinity` | session-pinned routing for multi-turn |
| `weighted_elo` | ELO-weighted selection from success/latency history |
| `circuit_chain` | sequential with open/half-open circuit breakers |
| `fifo_matrix` | bounded FIFO queue (back-pressure) |

## Sovereign MCP gateway (:25120)

`router/sovereign-mcp-gateway/` is a trust boundary in front of upstream MCP servers: per-upstream circuit breakers quarantine poisoned servers, `notifications/initialized` pins sticky sessions, and `tools/list` is served as a provenance-namespaced union (`<upstream>__<tool>`) with 502 failover. Supervisor wiring is in progress — the code lives here, not yet under pitchfork.

## Relationship to herd

Herd owns local inference (`:25100`). Mesh owns routing and federation, and points at herd as the local leg:

```yaml
openai-compatible:
  baseUrl: http://127.0.0.1:25100/v1
```

## Verify

```bash
curl -sf http://127.0.0.1:25127/health    # shep (MCP federation)
curl -sf http://127.0.0.1:25115/health    # mesh-hub (discovery)
curl -sf http://127.0.0.1:25104/health    # sovereign-router
curl -sf http://127.0.0.1:25100/v1/models  # herd (local inference)
```

## Ops notes (2026-09-17)

- mesh-hub (:25115) was down and was brought back up via pitchfork (pitchfork start mesh-hub).
  /health returns 200. If pitchfork shows herd as errored while :25100 serves 200,
  that is stale supervisor ownership -- the healthy detached daemon holds the port; do not
  kill it or start a second instance.
- config.yml line 65 declares default: openrouter/inclusionai/ling-3.0-flash-fin:free:high,
  but nothing consumes it -- declared intent, not active routing. The live free pool is
  freeCandidates() in router/sovereign-router-ts/router_config.ts. Ling stays out of it
  until it passes the gate in docs/free-tier-models.md (currently 4/5 empty completions).

## Gemini API Tool Retrieval EAP

- The Gemini API Early Access Program for Tool Retrieval (Guillaume Vernade, giom@google.com)
  is directly relevant to shep: defer_loading: true offloads tool schemas server-side and a
  retrieval meta-tool lets the model search a large tool catalog dynamically -- designed for
  30+ tool catalogs, exactly the shape of shep (30 upstream MCP servers). Docs:
  https://ai.google.dev/gemini-api/docs/tool-retrieval
- Platform fixes confirmed by Google (2026-09-07): HTTP 400 on deferred tools with parameters
  fixed fleet-wide; token-accounting fix for uncalled deferred tools rolling out.
- Integration target: route Gemini tool-heavy traffic through the native google provider
  (generativelanguage.googleapis.com/v1beta/openai, already live in sovereign-router-ts)
  with deferred loading when the served catalog is large. Full integration needs the doc
  details -- not yet done.
