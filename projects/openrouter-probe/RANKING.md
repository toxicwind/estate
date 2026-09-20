# OpenRouter abstract-probe ranking — 2026-09-20

Probe: `openrouter-probe/probe_abstract.py`. Every model on OpenRouter's
`/v1/models` (446 IDs) got the same abstract prompt, **twice** (14:25 and
14:29 MDT — a background agent re-ran the sweep; both runs used the same
key, differences are temporal rotation):

> Output exactly: ABSTRACT-7X3Q. No other text.

Score 2 = exact match, 1 = contains the token, 0 = anything else.
Sorted score desc, latency asc. This ranking is **speculative** — it measures
instruction-following on a trivial abstract task, not quality. But it answers
the only question that matters first: *which models actually respond.*

## The :free suffix is an unreliable narrator

`/v1/models` listed 445 IDs. Live results:

| http | count | meaning |
|------|-------|---------|
| 402 | 346 | paid models, no credits on this account |
| 404 | 78 | dead / unavailable IDs |
| 200 | 15 | answered |
| 429 | 4 | throttled (transient) |
| 403 | 2 | refused |

Of the 15 HTTP-200s, only **8** produced usable content. Several `:free`
models return 200 with **empty bodies** (`ling-3.0-flash-vl:free`,
`ling-3.0-flash-fin:free`, `poolside/laguna-xs-2.1:free` at low max_tokens).
Trust the probe, not the suffix.

## Speculative ranking (union of both probes, verified live 2026-09-20)

| # | model | score | best latency | notes |
|---|-------|-------|--------------|-------|
| 1 | `nex-agi/nex-n2.5-mini:free` | 2 | 442ms | fastest exact match, both probes |
| 2 | `poolside/laguna-s-2.1:free` | 2 | 586ms | exact (needs max_tokens>=100) |
| 3 | `cohere/north-mini-code:free` | 2 | 612ms | exact (needs max_tokens>=100) |
| 4 | `nex-agi/nex-n2.5-pro:free` | 2 | 615ms | exact, both probes |
| 5 | `inclusionai/ling-3.0-flash-sante:free` | 2 | 758ms | exact, both probes |
| 6 | `nvidia/nemotron-3-ultra-550b-a55b:free` | 2 | 1157ms | **resurrected** — documented 503/EOL since 09-14, serving free again (2nd probe) |
| 7 | `nvidia/nemotron-3-super-120b-a12b:free` | 2 | 1829ms | exact, both probes |
| 8 | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | 2 | 1990ms | exact; reasoning model, needs token headroom (1st probe) |
| 9 | `nvidia/nemotron-3.5-lightning:free` | 1 | 2496ms | works but chatty — emits thinking process |
| — | `google/gemma-4-31b-it:free` | 0 | 429 | throttled during probes, was healthy before — kept as fallback |
| — | `openrouter/free` | 2 | 35215ms | OpenRouter auto-router, exact but 35s — excluded, too slow |

## Wiring decision

`herd.yaml` `openrouter-free` peer now lists the ranking in order (score 2 by
latency, then score 1, then the 429-fallback). Verified end-to-end:
`herd → keypool :25109 → OpenRouter` returns 200 for the top model with the
peer prefix correctly stripped (`openrouter-free/nex-agi/nex-n2.5-mini:free`).

## Operational notes

- **Probe caused a 402 storm.** The 8-worker full sweep tripped OpenRouter
  abuse detection: all keypool keys went `down` (402) for ~5 min during the
  probe, recovering automatically. Future sweeps: fewer workers.
- **max_tokens matters.** `max_tokens=30` false-negatived 3 of the 8
  (empty/truncated/error). `max_tokens=100` is the minimum honest probe.
  The old `max_tokens=5` "say OK" sweep is retired for this reason.
- **Keys are dynamic.** `bin/herd-keypool.py` parses `/home/toxic/.secrets`
  at startup + SIGHUP; `OPENROUTER_API_KEY_FREE` (Chris's free-models key)
  is live in the pool. No key material in config, ever.
- Raw data: `abstract-20260920-142518.jsonl`, `ranking-20260920-142518.json`,
  `reverify-20260920.jsonl` in this directory.
