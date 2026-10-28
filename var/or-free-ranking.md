# OpenRouter Free-Key Model Ranking (2026-09-20)

Probe: abstract prompt sent to **all 446** OpenRouter catalog models via the FREE key, with correct per-model request shapes (adaptive max_tokens/max_completion_tokens, adaptive temperature removal, reasoning-field capture, 2048-token budget re-probe for reasoning models whose thinking exhausted the small budget).

Abstract prompt: "Explain recursion in exactly three sentences for a smart 12-year-old, with one concrete real-world example."

**SPECULATIVE**: the quality ranking below is a single-prompt probe, not a benchmark. One answer per model, graded by LLM judges (nex-agi/nex-n2.5-pro:free, openrouter/free) plus a heuristic sentence check. Treat order as a rough signal, not a verdict.

## Tier 1: Working + answered the abstract prompt (15)

| Latency | Model |
|---------|-------|
| 1248ms | openrouter/free |
| 1395ms | nex-agi/nex-n2.5-mini:free |
| 1979ms | liquid/lfm-2.5-2.6b:free |
| 3085ms | inclusionai/ling-3.0-flash-fin:free |
| 3171ms | nex-agi/nex-n2.5-pro:free |
| 3283ms | inclusionai/ling-3.0-flash-vl:free |
| 3321ms | inclusionai/ling-3.0-flash-sante:free |
| 3359ms | nvidia/nemotron-3.5-content-safety:free |
| 8050ms | nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free |
| 9252ms | nvidia/nemotron-3-ultra-550b-a55b:free |
| 9908ms | cohere/north-mini-code:free |
| 11044ms | poolside/laguna-s-2.1:free |
| 19080ms | nvidia/nemotron-3-super-120b-a12b:free |
| 19563ms | nvidia/nemotron-3.5-lightning:free |
| 20771ms | dots-studio/dots-3-note-preview:free |

## Tier 2: Working but empty/unusable content (1)

Responded 200 but produced no gradeable answer (reasoning-only output, empty content, or refusal) even after a 2048-token re-probe.

| Latency | Model | Note |
|---------|-------|------|
| 237ms | poolside/laguna-xs-2.1:free | reprobe: {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"poolside/laguna-xs-2.1:f |

## Tier 3: Rate-limited, probably available (5)

429 on probe + fast retry + 2048-token re-probe; throttled, not dead.

- google/gemma-4-26b-a4b-it:free
- google/gemma-4-31b-it:free
- poolside/laguna-xs-2.1:free
- qwen/qwen3.8-27b:free
- z-ai/glm-5.2:free

## Not available on free key

- 346 models: 402 (paid, key is free-only)
- 78 models: 404 (stale/dead IDs)
- 2 models: 403 (forbidden)
- 0 models: 400 malformed (rejected even shape-adapted requests)
- 0 models: timeout / transport error

## Speculative quality ranking (abstract-prompt probe)

**SPECULATIVE — single-prompt probe, not a benchmark.** Each model answered the recursion prompt once; LLM judges graded each answer 0–10 on: exactly-three-sentences (0–3), correctness (0–3), concrete real-world example (0–2), fit for a smart 12-year-old (0–2). HeurSent = automated sentence count as a cross-check (3 = nailed the constraint).

| Rank | Score | HeurSent | Latency | Model | Judge verdict |
|------|-------|----------|---------|-------|---------------|
| 1 | 10/10 | 3 | 1248ms | openrouter/free | Excellent: clear, correct, concrete, and age-appropriate. |
| 2 | 10/10 | 3 | 3085ms | inclusionai/ling-3.0-flash-fin:free | Exactly three clear sentences with a fitting example. |
| 3 | 10/10 | 3 | 3171ms | nex-agi/nex-n2.5-pro:free | Exactly three clear, accurate, age-appropriate sentences. |
| 4 | 10/10 | 3 | 3283ms | inclusionai/ling-3.0-flash-vl:free | Clear, correct, exactly three sentences with a concrete example. |
| 5 | 10/10 | 3 | 3321ms | inclusionai/ling-3.0-flash-sante:free | Exactly three clear sentences with a concrete example. [rejudge] |
| 6 | 10/10 | 3 | 8050ms | nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free | Exactly three clear, accurate sentences with a concrete example. |
| 7 | 10/10 | 3 | 9908ms | cohere/north-mini-code:free | Clear, accurate, concrete, and age-appropriate. |
| 8 | 10/10 | 3 | 11044ms | poolside/laguna-s-2.1:free | Exactly three clear sentences with a fitting concrete example. |
| 9 | 10/10 | 3 | 20771ms | dots-studio/dots-3-note-preview:free | Clear, correct, exactly three sentences, and age-appropriate. |
| 10 | 7/10 | 2 | 1395ms | nex-agi/nex-n2.5-mini:free | Two sentences, missing third; explanation is clear and age‑appropriate. [rejudge] |
| 11 | 2/10 | 1 | 1979ms | liquid/lfm-2.5-2.6b:free | Incomplete, not three sentences, and lacks a concrete example. |
| 12 | 2/10 | 18 | 9252ms | nvidia/nemotron-3-ultra-550b-a55b:free | heuristic-only (judge call failed) |
| 13 | 2/10 | 17 | 19080ms | nvidia/nemotron-3-super-120b-a12b:free | heuristic-only (judge call failed) |
| 14 | 0/10 | 1 | 3359ms | nvidia/nemotron-3.5-content-safety:free | No recursion explanation, example, or three-sentence response provided. |
| 15 | 0/10 | 1 | 19563ms | nvidia/nemotron-3.5-lightning:free | Unrelated fragment; no explanation or example. |

## Notes

- The `:free` suffix remains unreliable as a sole signal: availability must be probed, not assumed from the label.
- Request shapes matter: models rejecting `temperature` or requiring `max_completion_tokens` were retried with adapted shapes before being classified; reasoning models were re-probed at 2048 tokens because 256 tokens were exhausted by thinking traces.
- Raw sweep data: var/or-free-sweep3.jsonl (JSONL) and var/or-free-sweep3-results.json (JSON array).
- Scripts: bin/or-free-sweep3.py (sweep), bin/or-free-grade.py (re-probe + judge + rank), bin/or-rejudge.py (judge fallback pass).
