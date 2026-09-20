# Provider Truth Table — 2026-09-20

**Thesis (Chris, validated):** Providers LIE. `/v1/models` listings advertise models that 404/402/empty-200/hang on actual invocation. Error messages lie. The ONLY truth is a real completion with actual content.

**Method:** Real completions with `max_tokens=100` (minimum). Lesson from Ling: reasoning models output to `reasoning` field before `content`; tiny-token probes (max_tokens=5) falsely report "empty". Every LIVE verdict = actual `FUZZ-LIVE` content returned.

## NIM (integrate.api.nvidia.com) — key: NVIDIA_API_KEY

| Model ID | Listed? | Actual HTTP | Content? | Latency | Verdict |
|---|---|---|---|---|---|
| moonshotai/kimi-k2.6 | YES | 404 | No | 109ms | **LYING** — "Function '23d4f03a-b8a6-4adb-a183-7daa083a09cc': Not found for account". EXACT reproduction of [NVIDIA forum #379257](https://forums.developer.nvidia.com/t/moonshotai-kimi-k2-6-returns-404-function-not-found-for-account-while-other-nim-models-work/379257) (same function ID!). Account-scoped enablement failure. |
| moonshotai/kimi-k3 | YES | TIMEOUT | No | 90s+ | **LYING** — Listed but hangs indefinitely. Matches reports of NIM Kimi queueing (minutes, ~5 tok/s). |
| moonshotai/kimi-k2-instruct | ? | 410 | No | — | GONE |
| kimi-k2-thinking | ? | 404 | No | — | NOT-FOUND |
| z-ai/glm-5.2 | ? | 410 | No | — | GONE (forum user got 200; our account differs) |
| meta/llama-3.1-8b-instruct | ? | 410 | No | — | GONE |

**NIM key status:** NIM_API_KEY → 401. NVIDIA_NIM_API_KEY → 401. NVIDIA_NIM_API_KEY_1 → 401. Only NVIDIA_API_KEY authenticates.

**GitHub pattern:** [opencodex research](https://github.com/lidge-jun/opencodex/blob/main/devlog/_fin/260715_issue126_nim_kimi/001_research.md) confirms: "/v1/models is catalog metadata, NOT an invocability list." 404 is account-scoped enablement, not auth failure.

## OpenRouter (OPENROUTER_API_KEY_1) — RE-FUZZED with max_tokens=100

**Previous sweep used max_tokens=5 — WRONG for reasoning models. Re-fuzz found 5 MORE live models.**

### NEWLY DISCOVERED LIVE (were "dead" in last sweep):

| Model ID | HTTP | Latency | Verdict |
|---|---|---|---|
| dots-studio/dots-3-note-preview:free | 200 | ~2s | **LIVE** — Real FUZZ-LIVE content |
| liquid/lfm-2.5-2.6b:free | 200 | ~1s | **LIVE** — Real FUZZ-LIVE content |
| cohere/north-mini-code:free | 200 | ~1s | **LIVE** — Real FUZZ-LIVE content |
| nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free | 200 | ~2s | **LIVE** — Reasoning model, works with adequate tokens |
| nvidia/nemotron-3-ultra-550b-a55b:free | 200 | ~3s | **LIVE** — Real FUZZ-LIVE content |
| nvidia/nemotron-3.5-content-safety:free | 200 | ~1s | **LIVE-WEAK** — Returns "User Safety" (safety classifier, working as designed) |

### Previously confirmed LIVE (still live):

| Model ID | Latency | Notes |
|---|---|---|
| nvidia/nemotron-3-super-120b-a12b:free | 489ms | Fastest |
| nex-agi/nex-n2.5-mini:free | 593ms | Steady |
| nex-agi/nex-n2.5-pro:free | 2307ms | Hangs on streaming |
| nvidia/nemotron-3.5-lightning:free | 86s | Very slow |
| inclusionai/ling-3.0-flash-vl:free | 885ms | Reasoning-first, insanely fast |
| inclusionai/ling-3.0-flash-fin:free | ~1s | Reasoning-first |
| inclusionai/ling-3.0-flash-sante:free | ~1s | Reasoning-first |

### Kimi on OpenRouter — ALL DEAD (confirmed with max_tokens=100):

| Model ID | HTTP | Verdict |
|---|---|---|
| moonshotai/kimi-k2 | 402 | NO-CREDITS |
| moonshotai/kimi-k2-0905 | 402 | NO-CREDITS |
| moonshotai/kimi-k2-thinking | 402 | NO-CREDITS |
| moonshotai/kimi-k2.5 | 402 | NO-CREDITS |
| moonshotai/kimi-k2.6 | 402 | NO-CREDITS |
| moonshotai/kimi-k2.7-code | 402 | NO-CREDITS |
| moonshotai/kimi-k3 | 402 | NO-CREDITS |

## Pollinations (anonymous, gen.pollinations.ai)

| Model ID | HTTP | Content? | Verdict |
|---|---|---|---|
| openai | 200 | YES ("OK") | **LIVE** |
| gpt-oss | **INCONSISTENT** | — | **LYING** — max_tokens=10 → HTTP 200 with reasoning stub. max_tokens=100 → 401 "API key required". Behavior changes with request params! |
| kimi-k3 | 401 | No | DEAD (key required) |
| moonshotai/kimi-k2.6 | 401 | No | DEAD (key required) |

## Mistral (MISTRAL_API_KEY, api.mistral.ai)

| Model ID | HTTP | Latency | Verdict |
|---|---|---|---|
| codestral-latest | 200 | 408ms | **LIVE** |
| mistral-medium-3.5 | 429 | — | RATE-LIMITED (not dead, retry later) |
| mistral-small-latest | 429 | — | RATE-LIMITED (not dead, retry later) |

## Moonshot Direct (MOONSHOT_API_KEY, api.moonshot.ai)

| Model ID | HTTP | Verdict |
|---|---|---|
| kimi-k2.6 | 429 | **VALID KEY, NO BALANCE** — "account suspended due to insufficient balance". The ONLY working Kimi route, one top-up away. |
| kimi-k2.7-code | (same account) | Same — needs balance |

## Summary: Kimi Routes

| Route | Status |
|---|---|
| Moonshot direct (kimi-k2.6, kimi-k2.7-code) | **ONE TOP-UP AWAY** — Key valid, account needs funds. Herd peer `moonshot` is wired and ready. |
| NIM (kimi-k2.6) | **LYING** — 404 function not enabled for account (reproduces forum) |
| NIM (kimi-k3) | **LYING** — Hangs indefinitely |
| OpenRouter (all 7 Kimi IDs) | **DEAD** — 402 insufficient credits |
| Pollinations (kimi-k3, kimi-k2.6) | **DEAD** — 401 key required |
| HF | **DEAD** — 401 (no working token) |

## Key Lessons

1. **Never trust `/v1/models`.** It's catalog metadata, not an invocability list. (NIM proves this.)
2. **Never trust max_tokens=5 probes.** Reasoning models need room to think. (Ling, dots, liquid, cohere, nemotron-reasoning prove this.)
3. **HTTP 200 ≠ working.** Pollinations returns 200 with 401 in the body. OpenRouter returns 200 with empty content for reasoning models starved of tokens.
4. **Error messages are account-scoped.** NIM's 404 "function not found for account" is not a broken model — it's a disabled entitlement.
5. **Behavior can be param-dependent.** Pollinations gpt-oss: 200 at max_tokens=10, 401 at max_tokens=100. Fuzz across params, not just models.

## Artifacts

- Fuzzer: `/home/toxic/sovereign/projects/provider-fuzz/fuzz.py` (reusable, max_tokens=100 default)
- This file: `/home/toxic/sovereign/projects/provider-fuzz/TRUTH.md`
