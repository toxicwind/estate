# Supported Models — flock (renamed from Astmatrix 2026-09-17)

> **NOTE 2026-09-19.** The cloud-provider table below is verified against
> `internal/flock/providers.go` (ELO values match). The KIMI and Local sections
> are stale: `kimi-auto` is a resolver-owned virtual model (see
> `/home/toxic/kimi-auto/herd.d/kimi-auto.yaml`), not an alias for K1.5, and the
> `local-fast` / `local-quality` / `local-longctx` IDs do not exist in the live
> `config/herd.yaml`. The in-process flock router itself was retired from the
> shipped binary 2026-09-17 — live cloud routing is the `flock:` delegation key
> to the `:8000` flock daemon.

## KIMI (Primary)
| Model | ID | Context | Speed | Use Case |
|-------|-----|---------|-------|----------|
| K1.5 | kimi/k1.5 | 128K | Fast | General purpose |
| Moonshot v1 128K | kimi/moonshot-v1-128k | 128K | Medium | Long context |
| Moonshot v1 8K | kimi/moonshot-v1-8k | 8K | Fast | Quick tasks |

Aliases: `kimi-auto` is a resolver-owned virtual model routing to the current best Kimi model (see `/home/toxic/kimi-auto/herd.d/kimi-auto.yaml`), not an alias for K1.5. The `kimi-long` / `kimi-fast` aliases below are unverified against the live config.

## Local (llama-swap) — RETIRED 2026-09-19

> These IDs (`local-fast`, `local-quality`, `local-longctx`) do not exist in the
> live `config/herd.yaml`. Local models are addressed by their config model IDs;
> cloud models appear in `/v1/models` with the `flock:` prefix.

| Model | ID | Context | Speed |
|-------|-----|---------|-------|
| Local Fast | local-fast | 32K | GPU |
| Local Quality | local-quality | 64K | GPU |
| Local Long CTX | local-longctx | 128K | GPU |

## Cloud Providers (13 total)
| Provider | Free Tier | Models | ELO |
|----------|-----------|--------|-----|
| OpenRouter | ✓ | auto, optimus-alpha | 1500 |
| Groq | ✓ | llama-3.1-70b, mixtral-8x7b | 1580 |
| GitHub | ✓ | Phi-4, gpt-4o-mini | 1500 |
| NVIDIA | ✓ | llama-3.1-nemotron-70b | 1550 |
| Cerebras | ✓ | llama-3.1-70b | 1560 |
| Hyperbolic | ✓ | llama-3.1-70b | 1490 |
| SiliconFlow | ✓ | deepseek-v2 | 1470 |
| Together | | llama-3.1-70b, mixtral-8x22b | 1520 |
| Fireworks | | llama-3.1-70b | 1510 |
| Mistral | | mistral-large-2 | 1530 |
| OpenAI | | gpt-4o, gpt-4o-mini, o1-preview | 1650 |
| Perplexity | | sonar | 1480 |

## Routing Strategies
- `hybrid` — Retry + circuit breaker + health check (default)
- `ast_race` — Parallel fan-out, first valid wins
- `sticky_affinity` — Session-based routing
- `weighted_elo` — ELO-weighted random selection
- `least_latency` — Route to lowest observed latency
- `round_robin` — Weighted round-robin
- `free` — Free-tier providers only
- `circuit_chain` — Chain through providers
