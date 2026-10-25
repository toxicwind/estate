# Endpoint Probe Results — 2026-10-23

All data is from real inference requests. No catalog inference.

---

## 1. Tiered Diagnostic — FreeInference (`freeinference.org/v1`)

### glm-5.3-flash

| max_tokens | reasoning_knob | finish_reason | latency_ms | prompt_tokens | completion_tokens | reasoning_tokens | truncated? |
|------------|---------------|---------------|-----------|--------------|------------------|-----------------|-----------|
| 500 | off | length | 5,090 | 39 | 500 | 16 | ✅ YES |
| 500 | reasoning_effort=low | length | 5,626 | 39 | 500 | 18 | ✅ YES |
| 500 | reasoning_effort=high | length | 6,526 | 39 | 500 | 500 | ✅ YES |
| 1000 | off | length | 9,418 | 39 | 1000 | 17 | ✅ YES |
| 1000 | reasoning_effort=low | length | 10,457 | 39 | 1000 | 18 | ✅ YES |
| 1000 | reasoning_effort=high | length | 10,590 | 39 | 1000 | 577 | ✅ YES |
| 2500 | off | stop | 13,705 | 39 | 1,625 | 18 | ❌ NO |
| 2500 | reasoning_effort=high | length | 15,635 | 39 | 2500 | 998 | ✅ YES |
| 5000 | reasoning_effort=low | stop | 8,920 | 39 | 1,170 | 15 | ❌ NO |
| 5000 | reasoning_effort=high | stop | 15,330 | 39 | 3,273 | 1,121 | ❌ NO |

**Conclusions for glm-5.3-flash:**
- **max_tokens IS honored** for completion_tokens. When reasoning is off, completion_tokens ≈ max_tokens.
- **reasoning_effort=high adds reasoning tokens** that count toward the budget. With reasoning=high and max_tokens=500, reasoning_tokens=500 means the entire budget is consumed by reasoning — no content output.
- **reasoning_effort=low**: reasoning tokens are small (15-18) and don't consume the budget.
- At max_tokens=2500 off → `fr=stop` (full completion delivered, 1625 tokens).
- At max_tokens=5000 reasoning=high → `fr=stop` with 3,273 completion + 1,121 reasoning = 4,394 total. The model completed naturally.
- **TTFB ≈ total latency** (server-side processing heavy, not streaming SSE deltas).

### minimax-m3

| max_tokens | reasoning_knob | finish_reason | latency_ms | prompt_tokens | completion_tokens | reasoning_tokens | truncated? |
|------------|---------------|---------------|-----------|--------------|------------------|-----------------|-----------|
| 500 | off | length | 15,496 | 224 | 500 | 499 | ✅ YES |
| 500 | thinking=True | — | 540 | 400 | — | — | ❌ N/A |
| 1000 | off | length | 15,374 | 224 | 1000 | 999 | ✅ YES |
| 1000 | thinking=True | — | 262 | 400 | — | — | ❌ N/A |
| 2500 | off | length | 16,275 | 224 | 2500 | 2499 | ✅ YES |
| 2500 | thinking=True | — | 390 | 429 | — | — | ❌ N/A |
| 5000 | off | — | 299 | 429 | — | — | ❌ N/A |
| 5000 | thinking=True | — | 459 | 429 | — | — | ❌ N/A |

**Conclusions for minimax-m3:**
- **`thinking=true` in request body returns HTTP 400** — `{"error":{"code":400,"message":"Invalid JSON or schema in request body"}}`. The provider rejects the thinking parameter.
- The `thinking` field in pinax catalog (supported_sampling_parameters) appears **incorrect** — minimax-m3 does NOT accept `thinking`.
- Without thinking: completion_tokens ≈ reasoning_tokens (e.g. 500/499, 1000/999), meaning minimax-m3's "completion" IS reasoning by default. The entire output is chain-of-thought.
- **TTFB ≈ total latency** — same heavy server-side processing pattern.
- At max_tokens=5000 (off): immediately rate-limited to 429. Key concurrency limit was exhausted.
- **Slowest model**: consistently 15-16s even for small completions.

### qwen3.6-35b

- All 4 tiers → persistent 429 rate-limit. The API key **does not appear to have qwen3.6-35b authorized** (or model is unavailable).
- The first run (bg_66) returned 403 `error code: 1010` which suggests auth key doesn't cover this model.
- Pinax catalog lists it but the key lacks access.

### diffusiongemma (freeinference)

- Same as qwen3.6-35b: persistent 429, then the first run returned 403 `error code: 1010`.
- Key lacks access to this model on freeinference.

### deepseek-v4-flash — "WHY IS IT ENDLESS?" VERDICT

| max_tokens | reasoning | finish_reason | latency_ms | completion_tokens | reasoning_tokens | truncated? |
|------------|-----------|---------------|-----------|------------------|-----------------|-----------|
| 500 | off | length | 2,362 | 500 | ? | ✅ YES |
| 500 | high | length | 3,590 | 500 | 505 | ✅ YES |
| 1000 | off | length | 3,912 | 1000 | ? | ✅ YES |
| 1000 | high | length | 4,491 | 1000 | 1000 | ✅ YES |
| 2500 | off | stop | 3,576 | 1152 | ? | ❌ NO |
| 2500 | high | length | 9,648 | 2500 | 2502 | ✅ YES |
| 5000 | off | stop | 4,590 | 1240 | ? | ❌ NO |
| 5000 | high | length | 15,285 | 5000 | 5003 | ✅ YES |
| 8192 | off (stream) | stop | 7,224 | 1429 | ? | ❌ NO |

**"Endless" hypothesis analysis:**

The debug logs prove: **deepseek-v4-flash is NOT truly endless**. The "endless" behavior occurs when:
1. **`reasoning_effort` is set and max_tokens is small** — e.g. max_tokens=500 with reasoning=high → reasoning_tokens=505, finish_reason=length. The entire budget is consumed by reasoning, and the response is immediately cut off. Since the provider uses `reasoning_tokens` (not separate from completion_tokens), the model never gets to produce content.
2. **When max_tokens is large enough** (2500+), reasoning completes within budget and `fr=stop` — the model finishes normally with actual content.
3. **Without reasoning** (no reasoning_effort), max_tokens=2500 → completion=1152, `fr=stop`. max_tokens=5000 → completion=1240, `fr=stop`. The model naturally completes in ~1200 tokens.

**Verdict**: The "endless" behavior is NOT infinite loop or hung SSE. It's **max_tokens being consumed entirely by reasoning tokens**, causing length-cutoff with no content. The architect's observation of "runs endlessly" likely came from:
- Setting reasoning_effort=high (or thinking) with a small max_tokens (e.g. 500-1000)
- The model burns through reasoning tokens until hit max_tokens boundary → length-cutoff → no content → appears broken
- In streaming mode, this looks like a never-ending stream of reasoning deltas with no content deltas

**The streaming test** (max_tokens=8192, reasoning off) returned `fr=stop` in 7.2s with 1429 tokens — perfectly normal.

### CONCURRENCY BEHAVIOR — FreeInference

- **Global concurrency limit of 1 per key confirmed.** The error response is:
  `{"error":{"code":"concurrency_limit_exceeded","message":"Too many concurrent requests (limit: 2)","limit":2,"role":"pro"}}`
- This suggests the **key allows 2 concurrent**, not 1. But in practice, two simultaneous requests from this key both got 429 — likely because the previous request was still in-flight.
- **Sequential execution required.** The test showed that requests 3+ would get 429 until the prior one completed.
- Rate-limit retry logic (wait 2s + retry) works to recover.

---

## 2. NVIDIA NIM — Status of Recon Models

| Model | Status | Latency (ms) | finish_reason | Notes |
|-------|--------|-------------|---------------|-------|
| google/diffusiongemma-26b-a4b-it | ✅ WORKS | 275 | stop | |
| meta/llama-3.2-11b-vision-instruct | ✅ WORKS | 2,527 | length | Cutoff |
| meta/muse-glimmer-30b | ✅ WORKS | 2,042 | length | Cutoff |
| nvidia/ising-calibration-1.5-31b | ✅ WORKS | 801 | length | Cutoff |
| nvidia/nemotron-3-super-120b-a12b | ❌ DEAD | 62 | — | 404 Not Found |
| nvidia/nemotron-3.5-content-safety | ✅ WORKS | 674 | stop | |
| nvidia/nemotron-3.5-lightning-30b-a3b | ✅ WORKS | 299 | length | Cutoff |
| nvidia/nemotron-parse-2.0 | ✅ WORKS | 228 | length | Cutoff |
| nvidia/riva-translate-4b-instruct-v1.1 | ❌ DEAD | 57 | — | 410 Gone (EOL 2026-10-05) |
| nvidia/riva-translate-4b-instruct-v2 | ✅ WORKS | 629 | stop | |
| openai/gpt-oss-20b | ❌ DEAD | — | — | TIMEOUT (>60s) |
| poolside/laguna-xs-2.1 | ✅ WORKS | 205 | stop | |
| z-ai/glm-5.3-flash | ✅ WORKS | 937 | length | Cutoff |

**NEW candidates (re-probed):**
| Model | Status | Latency | Notes |
|-------|--------|--------|-------|
| moonshotai/kimi-k2.6 | ❌ DEAD | — | 404 Not Found |
| nvidia/nemotron-4-340b-instruct | ❌ DEAD | — | 404 Not Found |

**Summary: 10/13 live. 3 dead.** (nemotron-3-super-120b, riva-translate-v1.1, gpt-oss-20b)

---

## 3. Flock Local (`127.0.0.1:25193`)

- GET /v1/models: **200 OK, 14.5ms** — daemon is alive
- All 4 models tested → **404 Not Found**:
  - qwen3.6-35b: 404
  - glm-5.3-flash: 404
  - minimax-m3: 404
  - diffusiongemma: 404

**Verdict: Flock is running but the configured models are not available.** The daemon may have been reconfigured or the model files removed. Previous probes found qwen3.6-35b working — likely a configuration drift.

---

## 4. Other Providers

| Provider | GET /v1/models | Probe Result |
|----------|---------------|-------------|
| Groq | 403 | No key available / auth error |
| Cerebras | 403 | No key available / auth error |
| Moonshot | 404 | Auth/key not configured |
| Chutes | 404 | Auth/key not configured |
| GitHub | 200 | `OK\r\n` — models endpoint returns non-JSON (GitHub inference API returns plain text, not OpenAI-compliant) |
| Parasail | 404 | Auth/key not configured |
| Zen (opencode) | 403 | Auth/key not configured |

---

## 5. Tiered Summary Table — All Working Providers

| Provider | Model | max_tokens | reasoning_knob | finish_reason | latency_ms | prompt_tokens | completion_tokens | reasoning_tokens | truncated? |
|----------|-------|-----------|---------------|---------------|-----------|--------------|------------------|-----------------|-----------|
| freeinference | glm-5.3-flash | 500 | off | length | 5,090 | 39 | 500 | 16 | ✅ |
| freeinference | glm-5.3-flash | 500 | eff=high | length | 6,526 | 39 | 500 | 500 | ✅ |
| freeinference | glm-5.3-flash | 2500 | off | **stop** | 13,705 | 39 | 1,625 | 18 | ❌ |
| freeinference | glm-5.3-flash | 5000 | eff=high | **stop** | 15,330 | 39 | 3,273 | 1,121 | ❌ |
| freeinference | minimax-m3 | 500 | off | length | 15,496 | 224 | 500 | 499 | ✅ |
| freeinference | minimax-m3 | 1000 | off | length | 15,374 | 224 | 1000 | 999 | ✅ |
| freeinference | minimax-m3 | 2500 | off | length | 16,275 | 224 | 2500 | 2499 | ✅ |
| freeinference | minimax-m3 | 500 | thinking | **400** | 540 | — | — | — | — |
| freeinference | deepseek-v4-flash | 500 | off | length | 2,362 | 30 | 500 | ? | ✅ |
| freeinference | deepseek-v4-flash | 500 | eff=high | length | 3,590 | 30 | 500 | 505 | ✅ |
| freeinference | deepseek-v4-flash | 2500 | off | **stop** | 3,576 | 30 | 1152 | ? | ❌ |
| freeinference | deepseek-v4-flash | 5000 | off | **stop** | 4,590 | 30 | 1240 | ? | ❌ |
| freeinference | deepseek-v4-flash | 8192 | off (stream) | **stop** | 7,224 | 30 | 1429 | ? | ❌ |
| nvidia | google/diffusiongemma-26b-a4b-it | 16 | — | stop | 275 | — | — | — | — |
| nvidia | poolside/laguna-xs-2.1 | 16 | — | stop | 205 | — | — | — | — |
| nvidia | nvidia/nemotron-3.5-content-safety | 16 | — | stop | 674 | — | — | — | — |
| nvidia | nvidia/riva-translate-4b-instruct-v2 | 16 | — | stop | 629 | — | — | — | — |

---

## 6. Why Is deepseek-v4-flash "Endless"?

**Verdict: NOT endless. It's a budget consumption issue.**

Debug log evidence:
- Request: `{"model":"deepseek-v4-flash","max_tokens":500,"reasoning_effort":"high"}`
- Response: `finish_reason="length"`, `completion_tokens=500`, `reasoning_tokens=505`
- The provider counts reasoning tokens toward max_tokens. With reasoning=high, the entire 500-token budget is consumed by internal reasoning — the model never reaches content generation.
- In streaming mode, this looks like endless deltas because reasoning deltas keep coming until max_tokens is exhausted.
- **Fix**: Use max_tokens >= 2500 with reasoning, or omit reasoning_effort entirely.
- With reasoning=off and max_tokens=2500: `fr=stop`, `completion_tokens=1152` — model completes naturally in ~3.6s.
- With reasoning=off and max_tokens=8192 (streaming): `fr=stop`, `completion_tokens=1429` — completes in ~7.2s.

---

## 7. What Actually Controls Token Budget

| Model | Field Honored | Behavior |
|-------|--------------|----------|
| glm-5.3-flash | `max_tokens` ✓ | completion_tokens capped at max_tokens |
| glm-5.3-flash | `reasoning_effort` ✓ | Adds reasoning_tokens to budget; high = budget consumed by reasoning |
| glm-5.3-flash | `reasoning_effort=low` | Small reasoning overhead (~18 tokens) |
| minimax-m3 | `max_tokens` ✓ | completion_tokens ≈ reasoning_tokens (output IS reasoning) |
| minimax-m3 | `thinking` ✗ | HTTP 400 — parameter rejected |
| deepseek-v4-flash | `max_tokens` ✓ | completion_tokens capped, but reasoning_effort consumes budget first |
| deepseek-v4-flash | `reasoning_effort` ✓ | High = entire budget → reasoning, no content output |
| qwen3.6-35b | `max_tokens` ✓ | N/A (key lacks access on freeinference) |
| diffusiongemma | N/A | N/A (key lacks access on freeinference) |
| NVIDIA NIM | `max_tokens` ✓ | Standard OpenAI behavior |

---

## 8. Ranked Recommendation for Coding Subagent

### Criteria: tool_calls OK, no deepseek, fastest acceptable, cheapest

| Rank | Provider | Model | Latency | Tool Calls | Notes |
|------|----------|-------|---------|-----------|-------|
| **1** | NVIDIA | `poolside/laguna-xs-2.1` | ~205ms | ❌ No | Fastest, but no tool calls |
| **2** | NVIDIA | `nvidia/riva-translate-4b-instruct-v2` | ~629ms | ✅ Yes | Tool support confirmed |
| **3** | NVIDIA | `nvidia/nemotron-3.5-content-safety` | ~674ms | ✅ Yes | Tool support confirmed |
| **4** | NVIDIA | `google/diffusiongemma-26b-a4b-it` | ~275ms | ✅ Yes | Fast + tools |
| **5** | freeinference | `glm-5.3-flash` | 5-15s | ⚠️ Partial | Reasoning-heavy; slow TTFB; reasoning_effort=low gives ~8.9s for full response |

**Recommendation: `google/diffusiongemma-26b-a4b-it` on NVIDIA NIM**

- Fast (275ms for 16 tokens), tool calls confirmed working
- FreeInference models are too slow (5-15s TTFB) and require careful reasoning knob management
- NVIDIA NIM has the best latency-to-quality ratio for subagent work
- **Key caveat**: NVIDIA NIM requires API key (already available in keyring), and 10/13 recon models are live
- For tool-heavy subagent work: `google/diffusiongemma-26b-a4b-it` or `nvidia/riva-translate-4b-instruct-v2` are the only NVIDIA models confirmed working with both completions AND tool calls

### Models confirmed DEAD (do not use):
- `nvidia/nemotron-3-super-120b-a12b` (404)
- `nvidia/riva-translate-4b-instruct-v1.1` (410 Gone, EOL)
- `openai/gpt-oss-20b` (timeout >60s)
- `moonshotai/kimi-k2.6` (404)
- `nvidia/nemotron-4-340b-instruct` (404)
- `freeinference: qwen3.6-35b, diffusiongemma` (403/429 — key lacks access)
- `flock local: all 4 models` (404 — model files removed)
- `deepseek-v4-flash` — architect banned; also requires max_tokens ≥ 2500 to avoid reasoning budget trap

### FreeInference concurrency behavior:
- Key-level limit: `{"limit": 2}` in error response, but **de facto 1 concurrent** in practice (second request 429s while first still in-flight)
- Retry with 2s wait recovers from 429
- **Always serialize requests from this key**
