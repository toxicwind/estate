# OpenRouter Free-Key Model Ranking (2026-09-20)

Probe: `Reply with exactly: PROBE-OK` (max_tokens 32, temp 0) sent to all 446
OpenRouter models via the FREE key. Sorted by instruction-following then latency.
Speculative: single-prompt probe, not a full quality eval.

## Tier 1: Working + exact instruction-following (13)

| Latency | Model |
|---------|-------|
| 325ms | poolside/laguna-xs-2.1:free |
| 327ms | cohere/north-mini-code:free |
| 470ms | nex-agi/nex-n2.5-mini:free |
| 555ms | nex-agi/nex-n2.5-pro:free |
| 567ms | nvidia/nemotron-3-super-120b-a12b:free |
| 570ms | liquid/lfm-2.5-2.6b:free |
| 680ms | inclusionai/ling-3.0-flash-fin:free |
| 867ms | inclusionai/ling-3.0-flash-sante:free |
| 929ms | openrouter/free |
| 1022ms | dots-studio/dots-3-note-preview:free |
| 1087ms | nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free |
| 2102ms | poolside/laguna-s-2.1:free |
| 2487ms | nvidia/nemotron-3-ultra-550b-a55b:free |

## Tier 2: Working but non-exact response (3)

Reasoning models or verbose formatters; they responded but did not emit
exactly `PROBE-OK` in content.

| Latency | Model | Note |
|---------|-------|------|
| 568ms | nvidia/nemotron-3.5-content-safety:free | safety-tuned, verbose |
| 1055ms | inclusionai/ling-3.0-flash-vl:free | reasoning in `reasoning` field |
| 4267ms | nvidia/nemotron-3.5-lightning:free | slow |

## Tier 3: Rate-limited, probably available (4)

429 on probe + retry; popular free models, throttled not dead.

- qwen/qwen3.8-27b:free
- z-ai/glm-5.2:free
- google/gemma-4-26b-a4b-it:free
- google/gemma-4-31b-it:free

## Not available on free key

- 346 models: 402 (paid, key is free-only)
- 78 models: 404 (stale/dead IDs)
- 2 models: 403 (forbidden)

## Notes

- The `:free` suffix is unreliable as a sole signal: 21 models carry it, but
  only 16 responded 200. Availability must be probed, not assumed from the label.
- nvidia/nemotron-3-super-120b-a12b:free and ultra-550b-a55b:free both work --
  large models available free.
- Raw probe data: var/or-free-sweep2.jsonl
