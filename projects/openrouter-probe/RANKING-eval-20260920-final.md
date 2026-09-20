# Eval ranking 20260920-final — final, 10 models (2026-09-20)

Instrument: GuideLLM fork (`toxicwind/guidellm`) + deterministic `instruction_following` scorer (sentinel `ABSTRACT-7X3Q`, thinking-strip on), real per-model HF tokenizers.
Prompt: `Output exactly: ABSTRACT-7X3Q. No other text.` — 6 requests/model, synchronous profile, max_tokens=300.
Ranking: quality mean desc, provider-free desc, latency p50 asc.
Quality aggregates cover COMPLETED requests only; transport-errored requests are scored for the record and excluded from quality means (provider failures are reliability signal, not quality signal).
Free status verified live against the OpenRouter catalogue (446 models, 24 provider-free at run time).

| rank | model | quality mean | n | err | lat p50 (s) | ttft p50 (ms) | out tok/s | tokenizer |
|---|---|---|---|---|---|---|---|---|
| 1 | nex-agi/nex-n2.5-mini:free | 2.00 | 6 | 0 | 0.41 | 362 | 26.0 | nex-agi/Nex-N2.5-mini |
| 2 | nex-agi/nex-n2.5-pro:free | 2.00 | 6 | 0 | 0.58 | 439 | 21.7 | nex-agi/Nex-N2.5-Pro |
| 3 | cohere/north-mini-code:free | 2.00 | 6 | 0 | 0.65 | 109 | 100.2 | CohereLabs/North-Mini-Code-1.0 |
| 4 | poolside/laguna-s-2.1:free | 2.00 | 6 | 0 | 0.93 | 622 | 5.7 | poolside/Laguna-S-2.1 |
| 5 | nvidia/nemotron-3-super-120b-a12b:free | 2.00 | 3 | 3 | 1.04 | 290 | 54.8 | nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16 |
| 6 | inclusionai/ling-3.0-flash-sante:free | 2.00 | 6 | 0 | 1.05 | 625 | 79.4 | inclusionAI/Ling-3.0-flash-Fin |
| 7 | nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free | 2.00 | 5 | 1 | 1.18 | 258 | 37.2 | nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16 |
| 8 | nvidia/nemotron-3-ultra-550b-a55b:free | 2.00 | 6 | 0 | 3.44 | 447 | 10.7 | nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-NVFP4 |
| 9 | nvidia/nemotron-3.5-lightning:free | 1.83 | 6 | 0 | 32.25 | 15936 | 4.7 | nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-NVFP4 |
| 10 | openrouter/free | 1.67 | 6 | 0 | 1.69 | 432 | 54.6 | gpt2 |

## Notes
- `openrouter/free` has no stable tokenizer; it ran on the explicitly labelled `gpt2` fallback and is NOT tokenizer-comparable with the rest.
- `nvidia/nemotron-3-super-120b-a12b:free`: 3/6 requests errored at the provider (excluded from the quality mean); quality 2.0 over 3 completed.
- `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`: 1/6 errored; quality 2.0 over 5 completed.
- 14 live-free models lack tokenizer mappings and were not probed (see run logs).
- Raw per-model GuideLLM JSON: `eval-<ts>-<model>.json` in this directory.
- Preliminary sweep `20260920-150006` (pre-fix fork code) is superseded by this ranking and not committed.
