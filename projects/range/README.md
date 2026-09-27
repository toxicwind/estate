# Range — Tool Federation & Ranch Domain Layer

`range/` holds the tool-federation and routing domain: service launchers,
domain config, and the `ranch/` monorepo.

---

## Layout

```text
range/
├── bin/                        # Service launchers and probes
├── config.yml                  # Unified range config — model roles, port mappings
└── ranch/                      # Monorepo (toxicwind/ranch)
    ├── stockyard/              # Routers (herd, flock, paddock, router-legacy)
    ├── barn/                   # MCP tools (gatehouse, browserless, gemini-mcp, secretsmith)
    ├── corral/                 # Multi-agent engineering engine (@sovereign/corral)
    ├── squawk/                 # File-based multi-agent markdown chat
    ├── squawk-ws/              # WebSocket bridge for squawk events
    ├── data/                   # Model discovery catalogs, package tables
    ├── research/               # Research scripts and extraction toolkits
    ├── docs/                   # Architecture and contract documentation
    └── ui/                     # Ranch web dashboard
```

Launchers in `bin/`: `landing.py`, `gatehouse-serve.sh`,
`openfang-mesh-probe.sh`.

---

## gatehouse — MCP federation (:25127)

**gatehouse** (renamed mcpproxy → shep → gatehouse, 2026-09-26) serves one
endpoint in front of **34 upstream MCP servers**: quarantine for new servers,
BM25 tool discovery, health checks, and security scanning.

| Setting | Value |
| :--- | :--- |
| **Live config** | `ranch/barn/gatehouse/mcp_config.json` — gitignored |
| **Template** | `ranch/barn/gatehouse/mcp_config.json.dist` — tracked, scrubbed |
| **Launcher** | `bin/gatehouse-serve.sh` — pitchfork daemon `gatehouse` |
| **Secrets** | `/home/toxic/.secrets`, injected at runtime |

gatehouse rewrites the effective config on every start, re-materializing live
secrets into `mcp_config.json`. That is why the live file is never tracked and
`.dist` is the tracked scrubbed template; the launcher bootstraps one from the
other on a fresh checkout. Running the binary directly, without
`MCPPROXY_API_KEY` from the secrets file, crash-loops.

Upstream is unchanged — `github.com/smart-mcp-proxy/mcpproxy-go`, binary
`cmd/mcpproxy` — so the `MCPPROXY_API_KEY` environment variable keeps its
upstream name. The local rename frees `shep` for the unrelated
[`shep-ai/shep`](https://github.com/shep-ai/shep) agent orchestrator.

---

## sovereign-router — TS multi-provider gateway (:25104)

The live multi-provider gateway: 7 providers (llama-swap, openrouter, nvidia,
groq, cerebras, google, mistral), 7 routing strategies, built-in `/ui`
dashboard. Source: `ranch/stockyard/router-legacy/sovereign-router-ts/`.

Override the strategy per request:

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

---

## Sovereign MCP gateway (:25120)

`ranch/stockyard/router-legacy/sovereign-mcp-gateway/` is a trust boundary in
front of upstream MCP servers: per-upstream circuit breakers quarantine
poisoned servers, `notifications/initialized` pins sticky sessions, and
`tools/list` is served as a provenance-namespaced union (`<upstream>__<tool>`)
with 502 failover.

**Not yet supervised.** The code is in the tree but is not wired into
pitchfork, and `:25120` is currently held by the `sovereign-chat` daemon.

---

## Relationship to herd

Herd owns local inference (`:25100`). Range owns routing and federation, and
points the agent config at herd as the local leg — `config/tau/config.yml`:

```yaml
openai-compatible:
  baseUrl: http://127.0.0.1:25100/v1
```

---

## Verify

```bash
for s in "gatehouse:25127/health" "mesh-hub:25115/health" \
         "sovereign-router:25104/health" "herd:25100/v1/models"; do
  printf '%-16s %s\n' "${s%%:*}" \
    "$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "http://127.0.0.1:${s#*:}")"
done
```

A healthy fleet prints `200` on all four.

---

## Ops notes — 2026-09-17

- mesh-hub (:25115) was down and was brought back up via pitchfork
  (pitchfork start mesh-hub). /health returns 200. If pitchfork shows herd as
  errored while :25100 serves 200, that is stale supervisor ownership — the
  healthy detached daemon holds the port; do not kill it or start a second
  instance.
- config.yml line 65 declares default:
  `openrouter/inclusionai/ling-3.0-flash-fin:free:high`, but nothing consumes
  it — declared intent, not active routing. The live free pool is
  `freeCandidates()` in
  `ranch/stockyard/router-legacy/sovereign-router-ts/router_config.ts`. Ling
  PASSED the gate 2026-09-17 (corrected 8/8 benchmark, warm TTFT < 2 s; earlier
  0/8 was a probe bug using the invalid double-prefixed model ID) and is now IN
  the pool: 14 candidates verified live, router restarted via pitchfork 04:25
  MDT, /health 200. See [docs/free-tier-models.md](../../docs/free-tier-models.md)
  for the full record.

---

## Gemini API Tool Retrieval EAP

- The Gemini API Early Access Program for Tool Retrieval (Guillaume Vernade,
  giom@google.com) is directly relevant to gatehouse: `defer_loading: true`
  offloads tool schemas server-side and a retrieval meta-tool lets the model
  search a large tool catalog dynamically — designed for 30+ tool catalogs,
  exactly the shape of gatehouse (34 upstream MCP servers). Docs:
  https://ai.google.dev/gemini-api/docs/tool-retrieval
- Platform fixes confirmed by Google (2026-09-07): HTTP 400 on deferred tools
  with parameters fixed fleet-wide; token-accounting fix for uncalled deferred
  tools rolling out.
- Integration target: NATIVE Gemini path -- POST /v1beta/interactions on
  gemini-flash-tool-retrieval with the EAP key (GEMINI_API_KEY_2), server-side
  mode with gatehouse's 34-server union as mcp_server entries + defer_loading:
  true. NOT the OpenAI-compat /v1beta/openai path (no EAP semantics there), and
  NOT nim-proxy. Full spec in
  [docs/gemini-tool-retrieval.md](../../docs/gemini-tool-retrieval.md);
  LLM-friendly API reference in
  [docs/gemini-tool-retrieval-reference.md](../../docs/gemini-tool-retrieval-reference.md).
  BLOCKED on depleted prepay credits -- Chris tops up at ai.studio/projects.

---

## squawk — fleet messaging (moved here 2026-09-19)

Squawk source used to live scattered at home root; it now lives here as
`ranch/squawk/` (fleet WhatsApp relay) and `ranch/squawk-ws/` (fleet WS push
server, `:25147`). pitchfork daemons `squawk-feed`, `squawk-ws` and
`squawk-ws-client` run out of those paths, alongside `squawk-relay-sink` and
`squawk-relay-forward`.

The systemd user unit `squawk-watchdog.timer` (enabled, 60 s) keeps the
pitchfork supervisor alive.

There are no home-root compat symlinks left to fix. `~/squawk` and
`~/squawk-ws` are both gone outright — no symlink entries at all at home
root, not dangling ones. The consumer that used to break on them has
already been repointed: `squawk-relay`'s `run-sink.sh` now defaults
`SQUAWK_CODE_DIR` to `/home/toxic/sovereign/projects/range/ranch/squawk`
instead of the dead `/home/toxic/squawk`, and the `squawk-relay-sink`
unit sets no `env`, so the script default is the live one.

The relay's port is not pinned in `pitchfork.toml` and the squawk docs use a
`127.0.0.1:n` placeholder, so it is deliberately left unstated here.
