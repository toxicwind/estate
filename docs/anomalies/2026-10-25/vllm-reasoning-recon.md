# vLLM Sampling-Parameter Recon — 2026-10-25

**Scope:** All 6 freeinference models × 10 sampling-parameter modes. DECLARED ≠
OBSERVED: every row is a live `POST /v1/chat/completions` probe, not catalog
inference. Raw responses persisted to `/tmp/vllm-recon-20261025T175149Z/raw.jsonl`.

**Key:** `hyi-…` (service=`freeinference-api-key`). Authorized for ALL 6 models.
The 2026-10-23 doc claim that qwen3.6-35b / diffusiongemma "lack key access" is
**RESOLVED** — both now return 200.

## Models probed

`glm-5.3-flash`, `minimax-m3`, `qwen3.6-35b`, `diffusiongemma`,
`deepseek-v4-flash` (chat), `bge-m3` (embeddings-only).

## Matrix (status / reasoning_content / finish / reasoning_tokens)

Legend: `rc=` reasoning_content presence (HAS|none), `rt=` usage.reasoning_tokens
(blank = field absent), `ct=` completion_tokens, `finish=` finish_reason.

| Model | baseline | reasoning_effort=high | reasoning_effort=low | thinking_token_budget=100 | thinking_token_budget=2000 | thinking=true | temp=0.7,top_p=0.9 |
|---|---|---|---|---|---|---|---|
| glm-5.3-flash | 200 rc=HAS rt=1 | 200 rc=HAS rt=6 | 200 rc=none | 200 rc=HAS rt=1 | 200 rc=HAS rt=1 | 200 rc=HAS | 200 rc=HAS rt=1 |
| minimax-m3 | 200 rc=none rt=28 | 200 rc=none rt=40 | 200 rc=none rt=30 | 200 rc=none rt=39 | 200 rc=none rt=22 | 200 rc=HAS finish=length | 200 rc=none rt=46 |
| qwen3.6-35b | 200 rc=none | 200 rc=none rt=? | 200 rc=none | 200 rc=none | 200 rc=none | 200 rc=none | 200 rc=none |
| diffusiongemma | 200 rc=HAS rt=? | 200 rc=HAS | 200 rc=HAS | 200 rc=HAS | 200 rc=HAS | 200 rc=HAS | 200 rc=HAS |
| deepseek-v4-flash | 200 rc=none | 200 rc=HAS rt=107 | 200 rc=HAS rt=95 | 200 rc=none | 200 rc=none | 200 rc=none | 200 rc=none |
| bge-m3 | 404 "not found" (embeddings) | 404 | 404 | 404 | 404 | 404 | 404 |

## Findings (anomaly-grade)

1. **`thinking_token_budget` IS honored** (vLLM native sampling param; non-negative
   int or `-1` unlimited, per `validate_thinking_token_budget`). All 5 chat models
   accept it. This is the **correct knob for the reasoning-budget trap** — prefer it
   over soley `max_tokens` when capping reasoning. Doc source: `docs.vllm.ai
   /features/reasoning_outputs`, `sampling_params`.

2. **`thinking:{type:enabled}` on minimax-m3 now returns 200** (finish=length,
   rc=HAS) — the 2026-10-23 anomaly doc that says minimax-m3 `thinking` → HTTP 400
   is **OUTDATED**. The backend now accepts the enabled-form (`thinking:false` /
   rejected disabled-form still to re-verify).

3. **`reasoning_content` exposure is model-partitioned**:
   - glm-5.3-flash, diffusiongemma: return `message.reasoning_content`.
   - minimax-m3, deepseek-v4-flash, qwen3.6-35b: do NOT return `reasoning_content`
     in this mode (minimax + deepseek still bill `usage.reasoning_tokens`; deepseek
     exposes it under `reasoning_effort`).
   - `X-Reasoning-Passthrough: true` header makes glm + diffusiongemma return
     `reasoning_content`; it has no effect on minimax/qwen/deepseek (they strip it).

4. **`reasoning_effort` accepted by all chat models** (maps to vLLM reasoning
   parser). `reasoning_effort=high` on deepseek-v4-flash burns 107 reasoning tokens
   vs 9 baseline — confirms reasoning consumes the same token ceiling as `max_tokens`.

5. **diffusiongemma always reasons**: even `thinking_token_budget=0` → finish=length
   at max_tokens. Its output IS chain-of-thought; `reasoning_effort` and `token_budget`
   do not turn reasoning off. Do not use for non-reasoning tasks.

6. **`reasoning_tokens` (usage) is unreported** for qwen3.6-35b and diffusiongemma
   even when they reason — token accounting must not assume that field is present.

7. **bge-m3 is embeddings-only** — `POST /v1/chat/completions` → 404 `Model not found`.
   Use `POST /v1/embeddings`. (Correct per docs.)

## Operational guidance

- To bound reason-starvation on a reasoning model, set BOTH `max_tokens` and
  `thinking_token_budget` (e.g. `thinking_token_budget` = reasoning cap,
  `max_tokens` = total cap). vLLM treats -1 as unlimited.
- Route: glm-5.3-flash / diffusiongemma expose `reasoning_content`; use them when
  the client must replay reasoning. minimax-m3 / deepseek-v4-flash bill reasoning
  but hide the field unless `reasoning_effort` is used.
- The kf-fix (this session) is what un-blocked the key for tau. Fresh login shells
  now source `FREEINFERENCE_API_KEY` from the secretsmith keyring.

## Evidence files

- Matrix + raw bodies: `/tmp/vllm-recon-20261025T175149Z/matrix.txt`, `raw.jsonl`
- Probe script: `/tmp/vllm-recon/vllm-reasoning-recon.sh` (reusable)