# Cold-start hang re-audit — why 4 NIM models go silent instead of failing fast

Date: 2026-09-14. Endpoint: `POST https://integrate.api.nvidia.com/v1/chat/completions`.
Question: 4 models accept the POST, then emit **zero bytes for 30s+** until the
client's read timeout — never a fast 404/503. Meanwhile `super-120b` 503s *fast*
under load. A hang is a different failure mode. Why?

## TL;DR

There is no single hang. Probing past the 30s client ceiling revealed **three
different failure signatures**, plus one model that recovered:

| Model | Past-30s behavior | Signature |
|---|---|---|
| `moonshotai/kimi-k3` | **Streams at ~40.5s** TTFT, then serves | cold 2.8T load and/or max reasoning trace |
| `mistralai/mistral-nemotron` | **HTTP 500 at ~22–35s**, `problem+json` | NVCF inference-connection error |
| `google/gemma-4-31b-it` | **Silent past 45s**, no error | wedged backend, no server timeout surfaced |
| `nvidia/ising-calibration-1.5-31b` | **200 in 1.3s** — recovered | transient cold; pool now warm |

The "cold-start crew" is not a fixed set. Ising went from timeout to 1.3s
between runs. The hang is what a **cold NVCF function pool** looks like from the
outside: the gateway (NVCF) accepts the invocation and holds the connection open
while the backend materializes — or fails to. Fast 404 = entitlement rejected at
the edge. Fast 503 = warm pool, saturated. Hang = no warm backend, cold path with
no client-visible timeout.

## Card evidence (full cards read)

**kimi-k3** (`cards/moonshotai__kimi-k3.md`):
- 2.8T-param MoE, 104B active, 896 experts, MXFP4 weights, 1M context.
- **"Thinking is always enabled."** Reasoning effort configurable low/high/max.
- Test hardware: **Grace Blackwell GB300x8** — the single most exotic hardware in
  the catalog. Trial-fleet capacity for this is near zero.
- Benchmarks used **max reasoning effort + temperature 1.0**.

**gemma-4-31b-it** (`cards/google__gemma-4-31b-it.md`):
- Thinking toggled by `<|think|>` system token; partner sampling
  **temperature=1.0, top_p=0.95, top_k=64**.
- 256K context, hybrid local/global attention.

**mistral-nemotron** (`cards/mistralai__mistral-nemotron.md`):
- 2025-era Mistral×NVIDIA, TensorRT-LLM/vLLM on Hopper. Nothing exotic.
  Its hang is the most surprising — this should be a warm, boring model.

**ising-calibration-1.5-31b** (`cards/nvidia__ising-calibration-1.5-31b.md`):
- Dense VLM on Gemma 4 31B, BF16, vLLM, H100x2. Suggested inference:
  **temperature=0.2, zero-shot max_tokens=8192**. Answered `Pong!` in 1.3s.

**Contrast — ultra-550b** (`cards/nvidia__nemotron-3-ultra-550b-a55b.md`):
- Reasoning ON by default ("first generating a reasoning trace"), configurable
  via `chat_template_kwargs: {enable_thinking, medium_effort, force_nonempty_content}`.
  Partner default: temperature=1.0, top_p=0.95, max_tokens=16000.
- Tool calls require `enable_thinking: true, force_nonempty_content: true` —
  consistent with our probe seeing **empty output, no tool calls** when those
  kwargs were absent.

**Contrast — nano-omni-reasoning**:
- Thinking-mode table: temperature 0.6, max_tokens 20480, **reasoning_budget
  16384**, grace_period 1024. Default reasoning budgets are enormous.

## Docs evidence (docs.api.nvidia.com, read deeply)

- The LLM API index page is **stale**: it still lists `deepseek-ai/deepseek-v4-pro`
  (delisted from `/v1/models` today) and `nvidia/nemotron-3-nano-30b-a3b` (410 EOL).
  Docs are a third unreliable narrator (catalog, headers, cards, docs — all differ).
- kimi-k3's endpoint schema exposes **`reasoning_effort`: enum [low, high, max],
  default `max`**. Quote: *"Controls how long the model reasons before answering…
  unset falls back to the model default (`max`)."* Sampling params (top_p,
  penalties, n) are **fixed by the model, not exposed**. Every default request
  burns a max-effort hidden reasoning trace before the first visible token.
- gemma-4's endpoint schema exposes a thinking/reasoning toggle plus
  `chat_template_kwargs.enable_thinking`.
- No public OpenAPI JSON exists (`/openapi.json` → 404); the reference pages are
  JS apps with embedded schemas.

## Probe results (bounded, ~3 min total)

Wave 1 — plain tiny non-streaming request, 20s timeout, card-recommended sampling:
- kimi-k3 (temp 1.0): **hang** (20.6s, zero bytes)
- gemma-4 (temp 1.0/top_p 0.95/top_k 64): **hang** (20.5s)
- mistral-nemotron (temp 0.7): **hang** (20.6s)
- ising (temp 0.2): **200 in 1.3s** — "Pong!"

Wave 2 — model-specific params:
- kimi-k3 `reasoning_effort=low`: **hang** (20.4s) — hang is param-independent at 20s
- gemma-4 `chat_template_kwargs.enable_thinking=false`: **hang** (20.5s)
- gemma-4 top-level `enable_thinking=false`: **hang** (20.5s)
- ising max_tokens=8192 (card value): **200 in 1.6s**
- mistral-nemotron fuller shape: **hang** (20.2s)

Wave 3 — streaming, 45s timeout (tests "slow cold load" vs "dead backend"):
- kimi-k3: **first byte at 40.5s**, 5+ chunks streamed. Alive — just catastrophically slow TTFT.
- gemma-4: **nothing at 45s**.
- mistral-nemotron: **HTTP 500 at 34.9s**.

Follow-up on the 500 (non-streaming, 60s timeout):
- HTTP 500 at 22.3s. Body: `{"type":"urn:inference-connection:problem-details:internal-server-error",
  "title":"Internal Server Error","status":500,
  "detail":"Inference connection error while making inference request"}`.
- Headers: `Content-Type: application/problem+json`, **`Nvcf-Status: errored`**.
- NVCF = NVIDIA Cloud Functions. The trial API is NVCF-fronted; the function
  errored *while connecting* to inference. The 22–35s delay is NVCF retry/backoff
  before surfacing.

Raw records: `data/coldstart_probes_2026-09-14.json` (waves 1–2; wave 3 in §Probe results).

## Ranked hypotheses

**H1 — Cold NVCF pool, no server-side queue timeout (strongest).**
Trial fleet keeps no warm replica for low-traffic models. NVCF accepts the
invocation and holds the connection while the backend cold-loads; the client's
timeout fires first. *Supports:* kimi streaming at 40s; ising recovering to 1.3s
(transient cold). *Would disprove:* a hang that never resolves at very long
timeouts (gemma-4 at 45s weakens H1 but doesn't kill it — a 2.8T-class load can
take minutes).

**H2 — Backend crash / unreachable on cold start.**
mistral-nemotron's `urn:inference-connection` 500: NVCF retried connecting for
~22–35s, then surfaced `Nvcf-Status: errored`. The backend for this model is
broken or missing, not merely cold. *Supports:* problem+json type URN names the
inference *connection*, not the model. *Would disprove:* eventual 200s on retry
(flapping 500→200 would mean transient).

**H3 — Max-effort hidden reasoning before first token.**
kimi-k3 defaults `reasoning_effort=max`, thinking always on; nano-omni's default
reasoning budget is 16384 tokens. First visible byte requires the full hidden
trace. *Supports:* docs default=max; 40s TTFT consistent with a giant trace.
*Weakened by:* `reasoning_effort=low` still hung at 20s (but low-effort was never
retested at 45s — open gap).

**H4 — Wedged backend, lost wakeup.**
gemma-4 silent past 45s with no error and no 500: routed to a backend that will
never respond, and NVCF surfaces no timeout. *Would disprove:* eventual bytes or
a late 500.

**Rejected:** "request shape / sampling params cause the hang" — param variations
(reasoning_effort=low, thinking off, card sampling) changed nothing at 20s.
**Rejected:** "entitlement" — 404-gated models fail fast; these pass the gate.

## What this means for the 5-second rule

- kimi-k3 is *usable* but never on a hot path: ~40s TTFT even when it works.
- mistral-nemotron is *broken*, not slow: expect 500s, not latency.
- gemma-4 is *unreachable* right now: silence, no error to catch.
- ising is *fine*: 1.3s. The "cold-start crew" membership is transient —
  re-probe before blacklisting.

## Open gaps

- kimi-k3 with `reasoning_effort=low` at 45s+ (does low effort fix the 40s TTFT?).
- gemma-4 at 5+ minutes (does it ever answer?).
- Whether mistral-nemotron's 500 flaps to 200 (transient) or is permanent.
- The `Nvcf-Reqid` header gives NVIDIA a traceable request id for any bug report.
