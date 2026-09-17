# Router comparison — all forms (2026-09-17)

Live router: `tools/sovereign-router/sovereign-router-ts/` on `:25104`.

## The forms

Three separate implementations have carried similar routing DNA:

1. **sovereign-router-ts** (Bun/TypeScript) — the **live production router**,
   pitchfork daemon on `:25104`. Live provider `/models` discovery, 7
   strategies, streaming, sticky sessions, ELO, circuits, HealthDB, free
   racing, `/ui` dashboard.
2. **Go cloud-router module** (`projects/herd/internal/astmatrix/`) — a
   llama-swap library module, not a version of #1. 13 providers,
   per-provider rate limits, request coalescing, least-latency and
   round-robin strategies, richer status surface. No live discovery, no
   streaming-first design.
3. **Mesh gateway cloud-router** (`projects/mesh/gateway/astmatrix.go`) —
   routes tool-call/MCP traffic, a different domain entirely (not model
   inference).

Stale copies of the TS tree exist at `projects/mesh/router/`,
`projects/herd/mesh/router/`, and a nested duplicate
`sovereign-router-ts/sovereign-router-ts/` — the live daemon runs from
`tools/sovereign-router/sovereign-router-ts/` only. The old TS User-Agent
and `[matrix]` log prefix were renamed to `Sovereign-Router/3.1` /
`[router]`; nothing of the old branding carries into the consolidated
router.

## Side by side

| | sovereign-router-ts (LIVE) | Go module |
|---|---|---|
| Location | `tools/sovereign-router/sovereign-router-ts/` | `projects/herd/internal/astmatrix/` |
| Status | **Production** — pitchfork daemon `:25104` | Library, compiled into herd llama-swap builds |
| Providers | 7: llama-swap (herd main port `:25100`), openrouter, nvidia (direct multi-key), groq, cerebras, google, mistral | 13: llama-swap, openrouter, nvidia, groq, together, cerebras, fireworks, hyperbolic, github, mistral, openai, perplexity, siliconflow |
| Strategies | 7: fifo, free, sticky, weighted, circuit_chain, hybrid, race | 8: hybrid, race, sticky, weighted, least_latency, round_robin, free, circuit_chain |
| Model discovery | **Live** — `GET {base}/models` per key at startup + every 30 min; union with curated | YAML-configured static lists |
| Health | SQLite WAL HealthDB, EMA latency, ELO, circuit breakers, sticky sessions | SQLite health DB, EMA latency, circuit breakers w/ half-open probes, sticky sessions |
| Rate limiting | NVIDIA multi-key token buckets (40 rpm/key, round-robin) | Per-provider token buckets (all providers) |
| Extra | SSE streaming, `/ui` dashboard, flap tracker, Prometheus `/metrics`, optional client-key auth | Request coalescing, latency histograms, richer status/metrics |

## Consolidation changes (this tree, 2026-09-17)

- **Live discovery authoritative**: `/v1/models` returns 779 unique servable
  IDs (was ~50 aliases); every provider-keyed model is directly addressable —
  no more curated-alias-only routing.
- **NVIDIA direct multi-key**: 4 keys, round-robin, 40-rpm token buckets per
  key. The old `flock` daemon (`:8000`, still running) is bypassed for NVIDIA
  by the router; other consumers unaudited so far.
- **Flap tracker**: 3 empty completions in 10 min benches a model from the
  free pool; strikes decay and re-probe. Visible at `/metrics`
  (`sovereign_router_model_empty_strikes`). Already striking flapping Ling
  variants on openrouter and llama-swap paths.
- **Substance guard on every path**: HTTP 200 with empty content (and no
  tool_calls) is a failure at every routing layer — never served, never
  sticky-pinned. Closed the circuit-chain/free fallback hole that served
  blank 200s.
- **`/v1/models` metadata**: provider, source (curated/live), free flag, ELO,
  circuit state, empty-strike count, plus raw provider objects where live.
- **Operational**: Prometheus `/metrics`, optional `SOVEREIGN_CLIENT_KEYS`
  auth, neutral naming (UA `Sovereign-Router/3.1`, `[router]` logs).
- **Local path preserved**: llama-swap provider routes through the herd main
  port `:25100`; the router has not bypassed it.

- **Free pool is live-metadata derived** (2026-09-17, Chris): `freeCandidates()`
  no longer enumerates a static `:free`-suffix list. Eligibility is
  `modelFree(p, mid)` — live `/models` pricing wins (OpenRouter prompt +
  completion priced `"0"` = free), with deterministic fallback to the `:free`
  suffix convention only when a provider exposes no pricing metadata at all.
  Filters: circuit state, flap strikes (substance-guard failures feed the
  strike counter), local llama-swap roles always join. `/v1/models`
  `x-sovereign.free` is the same function, so the catalog and the router
  agree. 4 live-free models the static list missed (`stealth/union-alpha`,
  `google/lyria-3-pro-preview`, `google/lyria-3-clip-preview`,
  `openrouter/free`) now race in the free pool.

## Spec limits (live tree, 2026-09-17)

| Limit | Value | Where |
|---|---|---|
| Free-pool race width | `MAX_PARALLEL = 4` | `router_config.ts` |
| Flap bench | 3 empty strikes in 600 s (`FLAP_STRIKES`/`FLAP_WINDOW_S`) | `router_matrix.ts` |
| Live discovery refresh | every 30 min + non-blocking at startup; 15 s fetch timeout | `router_live_models.ts` |
| Race timeout | 95 s gather-then-pick | `router_strategy.ts` |
| Provider call timeout | 120 s non-stream, 180 s stream | `router_strategy.ts` |
| NVIDIA direct | 4 keys round-robin, 40 rpm token bucket per key | `router_matrix.ts` |
| FIFO queue depth | `FIFO_MAX = 64` | `router_config.ts` |
| Sticky TTL | `STICKY_TTL = 1800` s | `router_config.ts` |
| Circuit open hold | 60 s, then half-open probe | `router_matrix.ts` |

## Remaining gaps (honest)

- TS router lacks 6 Go-module providers: together, fireworks, hyperbolic,
  github, openai, perplexity, siliconflow. Go module lacks google (Gemini).
- TS router has no request coalescing and no least-latency / round-robin
  strategies; per-provider rate limits exist only for NVIDIA.
- Flap strikes are in-memory (lost on restart); no echo/junk scoring yet.
- NVIDIA bucket exhaustion falls back to the default key instead of
  queueing; `/models` discovery uses only the first key.
- `/v1/models` deduplicates by model id, hiding multi-provider routes.

## Live discovery numbers (2026-09-17)

| Provider | Curated | Live | Union served |
|---|---|---|---|
| llama-swap | 3 | 102 | 102 |
| openrouter | 11 | 444 | 451 |
| nvidia | 12 | 82 | 92 |
| groq | 6 | 13 | 17 |
| cerebras | 0 | 2 | 2 |
| google | 4 | 59 | 60 |
| mistral | 4 | 46 | 47 |

`cerebras` was hardcoded to **zero** models before live discovery.
