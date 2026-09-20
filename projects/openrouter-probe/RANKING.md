# OpenRouter abstract-probe ranking — v3 (2026-09-20 ~14:55 MDT)

**This ranking is explicitly SPECULATIVE.** It measures instruction-following
on one trivial abstract task, not model quality, reasoning ability, or fitness
for any real workload. It answers exactly one question: *which model IDs
actually return the exact string they were asked for, repeatedly.*

## Method (v3 — supersedes all earlier sweeps)

- Script: `openrouter-probe/probe_reliability.py`
- Every ID on OpenRouter `/v1/models` (446 IDs), **3 sequential full passes**
  (1,338 attempts), 10 workers, no artificial sleeps or pacing
- Prompt, identical every trial: `Output exactly: ABSTRACT-7X3Q. No other text.`
- Credential: `OPENROUTER_API_KEY_FREE` (the free-models-only key), read
  in-process; value never logged
- Scoring: **2** = body is exactly `ABSTRACT-7X3Q`; **1** = contains it plus
  other text; **0** = anything else
- HTTP 200 with an empty body is classified `200-empty` and is **never**
  ranked as usable
- Rank key: exact-match rate desc, best score desc, p50 latency of exact hits asc

## Attempt distribution (1,338 attempts)

| class | count | meaning |
|-------|-------|---------|
| 402-not-entitled | 1,038 | paid models; the free key is not entitled. Expected, not an attack signal. |
| 404-dead-id | 234 | catalog IDs that don't resolve to a serving model |
| 429-throttled | 14 | transient throttling |
| 200-empty | 12 | 200 with an empty body — never usable |
| 403-refused | 6 | refused |
| http-529 | 1 | upstream overloaded (single event) |

Only **10 distinct IDs** returned the token at least once across 3 passes.
The `:free` suffix is an unreliable narrator: most `:free` IDs 404, 402, or
return empty 200s.

## Speculative ranking (v3, exact_rate desc / p50 asc)

| # | model | exact | p50 | mean | p99 | notes |
|---|-------|-------|-----|------|-----|-------|
| 1 | `cohere/north-mini-code:free` | 3/3 | 557ms | 555ms | 565ms | fastest AND most reliable; tight latency band; reasoning model — needs max_tokens headroom (50 truncated mid-thought, 300 clean) |
| 2 | `nex-agi/nex-n2.5-pro:free` | 3/3 | 583ms | 601ms | 659ms | |
| 3 | `nex-agi/nex-n2.5-mini:free` | 3/3 | 609ms | 747ms | 1173ms | |
| 4 | `inclusionai/ling-3.0-flash-sante:free` | 3/3 | 941ms | 936ms | 1028ms | |
| 5 | `nvidia/nemotron-3-super-120b-a12b:free` | 3/3 | 1349ms | 2206ms | 4478ms | |
| 6 | `nvidia/nemotron-3-ultra-550b-a55b:free` | 3/3 | 6088ms | 27588ms | 73939ms | reliable but capacity-constrained: min 1352ms / max 75324ms |
| 7 | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | 2/3 | 1630ms | — | — | 1× 200-empty |
| 8 | `poolside/laguna-s-2.1:free` | 2/3 | 2060ms | — | — | 1× http-529 |
| 9 | `openrouter/free` | 1/3 | 600ms | — | — | 1× 429-throttled, 1× contains-only; auto-router, latency varies wildly |
| 10 | `nvidia/nemotron-3.5-lightning:free` | 0/3 | — | — | — | 3/3 contains-only (emits thinking); unusable for exact-output tasks |

Notable demotions vs the census (var/or-free-ranking.md):
- `inclusionai/ling-3.0-flash-fin:free` and `ling-3.0-flash-vl:free`
  (census #2/#4): **200-empty on all 3 v3 trials** — they don't follow the
  instruction at all. Demoted.
- `dots-studio/dots-3-note-preview:free` (census #9): 200-empty ×3.
- `liquid/lfm-2.5-2.6b:free`: responds without error but never emitted the
  token in 3 trials — fails instruction-following, not availability.
- `google/gemma-4-31b-it:free`, `gemma-4-26b-a4b-it:free`, `qwen/qwen3.8-27b:free`,
  `z-ai/glm-5.2:free`: **429-throttled on all 3 v3 passes** — kept as
  throttled-fallback tier only; the keypool's cooldown/auto-recovery makes
  them safe there.

## Wiring decision

`herd.yaml` `openrouter-free` peer model order now follows the v3 table
(tiers 1–4). Tiers 2–4 exist because the keypool fails over across keys and
respects `down_until`/cooldown — a miss or throttle on one model routes to
the next instead of failing the call.

## Operational notes (corrected)

- **402 is entitlement, not abuse.** The earlier note claiming the probe
  "tripped OpenRouter abuse detection" was unproven causality and is
  retracted. 402 = the free key isn't entitled to paid models; that's the
  whole story. Throttles are 429s and are transient.
- **200-empty is a distinct failure mode.** Several `:free` IDs answer 200
  with empty bodies on every trial. They are live endpoints that don't
  follow instructions — worse than a clean 404 for routing purposes.
- **Keys are dynamic.** `bin/herd-keypool.py` parses `/home/toxic/.secrets`
  at startup + SIGHUP; `OPENROUTER_API_KEY_FREE` serves free models only
  (enforced in pick, failover, and recovery sweep). No key material in
  config, ever.
- **Single-pass sweeps are retired.** The 14:25/14:29 single-pass runs are
  superseded by v3 (3 passes). Don't cite their latencies as stable.

## Raw data

- `reliability-20260920-144532.json` — full v3 results (per-model exact
  rates, latency distributions, error classes)
- `abstract-20260920-142518.jsonl`, `abstract-20260920-142947.jsonl`,
  `ranking-20260920-142947.json` — superseded single-pass runs (kept for
  the record, not for wiring)
