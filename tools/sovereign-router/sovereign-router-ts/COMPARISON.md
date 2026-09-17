# Router vs AstMatrix — comparison (2026-09-17)

## The naming confusion, cleared up

"AstMatrix" is the name of the **Go** cloud-provider routing module
(`projects/herd/internal/astmatrix/`) built for llama-swap. The **TypeScript**
router (`tools/sovereign-router/sovereign-router-ts/`, the live one on
`:25104`) borrowed the name in its User-Agent (`SovereignASTMatrix/3.1`) and
`[matrix]` log prefix. They are **separate implementations**, not two versions
of one thing. There are also stale copies of the TS router tree at
`projects/mesh/router/`, `projects/herd/mesh/router/`, and a nested duplicate
`sovereign-router-ts/sovereign-router-ts/` — the live daemon runs from
`tools/sovereign-router/sovereign-router-ts/` only.

## Side by side

| | sovereign-router-ts (LIVE) | AstMatrix (Go module) |
|---|---|---|
| Language/runtime | Bun/TypeScript | Go (llama-swap module) |
| Location | `tools/sovereign-router/sovereign-router-ts/` | `projects/herd/internal/astmatrix/` |
| Status | **Production** — pitchfork daemon `:25104` | Library, compiled into herd llama-swap builds |
| Providers | 7: llama-swap, openrouter, nvidia (via local nim-proxy `:8000`), groq, cerebras, google, mistral | 13: llama-swap, openrouter, nvidia, groq, together, cerebras, fireworks, hyperbolic, github, mistral, openai, perplexity, siliconflow |
| Strategies | 7: fifo_matrix, ast_race, sticky_affinity, weighted_elo, circuit_chain, hybrid, free | 8: hybrid, ast_race, sticky_affinity, weighted_elo, least_latency, round_robin, free, circuit_chain |
| Model discovery | **Live** — `GET {base}/models` per key at startup + every 30 min (`router_live_models.ts`); curated list ∪ live | YAML-configured static lists |
| Health | SQLite WAL HealthDB, EMA latency, ELO scores, circuit breakers, sticky sessions | SQLite health DB, EMA latency, circuit breakers w/ half-open probes, sticky sessions |
| Extra features | FIFO depth cap (64), SSE streaming, `/ui` dashboard | Request coalescing, per-provider token-bucket rate limits, latency histograms, `/astmatrix/status` + `/metrics` |
| Config | `router_config.ts` + env (`~/.secrets`, `ports.env`) | `astmatrix_config.yaml` |

## Gaps worth knowing

- TS router is missing 6 AstMatrix providers: together, fireworks, hyperbolic,
  github, openai, perplexity, siliconflow. AstMatrix is missing google (Gemini).
- TS router has no per-provider rate limiting or request coalescing; AstMatrix
  has no live model discovery and no streaming-first design.
- `cerebras` was hardcoded to **zero** models in the TS router until the live
  discovery change — it now serves its 2 live models.

## Live discovery numbers (2026-09-17, first refresh)

| Provider | Curated | Live | Union served |
|---|---|---|---|
| llama-swap | 3 | 102 | 102 |
| openrouter | 11 | 444 | 451 |
| nvidia | 12 | 82 | 92 |
| groq | 6 | 13 | 17 |
| cerebras | 0 | 2 | 2 |
| google | 4 | 59 | 60 |
| mistral | 4 | 46 | 47 |

`/v1/models` on `:25104` now returns **779** unique servable IDs (was ~50
aliases). `/health` reports per-provider `live_models` + `live_status`.
