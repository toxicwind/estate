# nim/ — Unified NIM API layer

All model calls in the merged swarm route through `nim/client.py`.

## Why this exists

The old repo scattered NIM access across `swarm/nvidia_swarm_transport.py`
(120s timeouts, stale default model, broken streaming) and the Drive
monoliths (simulated clients that never called NVIDIA). This package is the
single, honest, fail-fast layer:

- **Fail-fast**: 5s default timeout, no retries. Chris's rule — anything over
  3–5s is useless in production.
- **Model-aware cold start**: kimi-k3 (~43s TTFT) and ultra-550b are known
  slow; they raise `ColdStartModelError` unless you explicitly opt in with
  `allow_cold_start=True`.
- **Dead models die early**: 404-gated legacy IDs and 410 EOL models raise
  `DeadModelError` *before* any network call, naming a live alternative.
- **Auth**: Secure Vault surrogate (sandbox) → `NVIDIA_API_KEY` env →
  clean `NimAuthError`. Raw keys are never logged, printed, or stored.
- **Honest diagnostics**: full response kept on the private result object;
  exceptions are sanitized (no bodies, no account ids).

## Model truth (2026-09-14 live audit)

`nim/models.py` encodes the 82-model fail-fast audit: 10 alive-fast, 55
dead-404-gated, rest timeout/503/other. The catalog is nondeterministic and
mutates (models delist silently), so re-verify with `client.models()` +
a tiny chat before scripting new ids.

Live general-chat picks: `openai/gpt-oss-20b` (default), `z-ai/glm-5.3-flash`.
`nvidia/nemotron-3-super-120b-a12b` is deprecated 2026-10-03 (503s).

## Sovereign seam

This client speaks plain OpenAI-compatible `/v1/chat/completions`, so it can
be registered as a **herd** upstream (herd = inference router, `:25100/v1`)
without changes. See `SOVEREIGN.md` at repo root.

## Usage

```python
from nim import NimClient, DEFAULT_MODEL

c = NimClient()  # 5s fail-fast
res = c.chat([{"role": "user", "content": "hello"}], model=DEFAULT_MODEL)
print(res["content"], res["latency_ms"])

# streaming
res = c.chat([...], stream=True)

# cold-start opt-in
res = c.chat([...], model="moonshotai/kimi-k3", allow_cold_start=True)

# async (needs NVIDIA_API_KEY env; surrogate is sync-only)
from nim import AsyncNimClient
ac = AsyncNimClient()
res = await ac.chat([...])
async for delta in ac.chat_stream([...]):
    ...
```
