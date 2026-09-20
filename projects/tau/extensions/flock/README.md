# tau-flock

Tau/omp extension that makes **flock** — the NVIDIA NIM OpenAI-compatible
proxy daemon on `127.0.0.1:8000` — first-class inside Tau sessions.

flock (renamed 2026-09-17 from `nim-proxy`) is herd's cloud-API completions
scaffold: local rate limiting, request history, operator dashboard, and an
OpenAI-compatible front that forwards upstream to
`https://integrate.api.nvidia.com/v1`. It never serves local models (that is
herd/llama-swap's job). The old `astmatrix` name is dead; everything is flock
now.

## What it adds

Slash commands (interactive):

| Command | Description |
|---|---|
| `/flock-status` | Daemon health + client config (base URL, key present/absent, timeout) |
| `/flock-models` | List models served by the proxy (requires API key) |
| `/flock-chat <prompt> [--model <id>] [--system <text>]` | Chat completion through flock |

LLM tools (the agent reaches for these instead of shelling out to curl):

`flock_status`, `flock_models`, `flock_chat`.

## Install

```bash
cd /home/toxic/sovereign/projects/tau/extensions/flock
bun install
tau plugin link .
```

## Env

- `FLOCK_BASE_URL` — proxy base URL (default `http://127.0.0.1:8000`)
- `FLOCK_API_KEY` — proxy client key (`Authorization: Bearer`). Optional;
  falls back to `NVIDIA_API_KEY` (flock accepts both as client keys). Required for
  `/v1/models` and `/v1/chat/completions`.
- `FLOCK_TIMEOUT_MS` — per-request timeout (default 60000, clamp 1000..600000)
- `FLOCK_DISABLED=1` — skip the extension
- `FLOCK_DEBUG=1` — stderr debug logging

## Typed errors

`src/flock.ts` throws `FlockError` with a `kind` of `network` | `timeout` |
`auth` | `http` | `api` | `empty`. The `empty` kind exists because the NIM
surface sometimes streams reasoning deltas and returns a blank 200 — an empty
completion is surfaced as an error, never a silent blank result.

## Live proof (2026-09-17, smoke run against live :8000)

```
== flock smoke test ==
base: http://127.0.0.1:8000
proxy API key: ABSENT from env (checked FLOCK_API_KEY, NVIDIA_API_KEY)
key-store check: /home/toxic/.secrets not present

-- GET /health
SMOKE PASS: /health -> ok
   measured: 5 ms

-- /v1/models (no key in env; reporting raw result)
   HTTP 401
   NOTE: /v1/models requires a proxy API key and none is present in env.
   Chat completions are untestable without it. Degraded to /health proof.

RESULT: DEGRADED — /health proven. /v1/models and /v1/chat/completions require FLOCK_API_KEY (absent).
```

Supporting surface checks:

- `curl http://127.0.0.1:8000/health` → `ok` (200)
- `curl http://127.0.0.1:8000/v1/models` without key → `401 {"code":"unauthorized","message":"missing or invalid proxy API key (Authorization: Bearer <redacted>)","type":"proxy_error"}` — the daemon's client-auth gate is live and functional
- flock daemon config (keyed client auth; confirmed by the 401 above) fronts upstream `https://integrate.api.nvidia.com` (per flock architecture docs)
- Sovereign router `http://127.0.0.1:25104/v1/models` → 200, **779 models** (independent surface check)
- `npx tsc --noEmit` → exit 0, zero errors

To run the full smoke (models + chat) with a key:

```bash
FLOCK_API_KEY='<redacted>' bash scripts/smoke.sh
```

The script prints the model id used and the first 200 chars of the completion,
and fails loudly (non-zero exit) if chat content comes back empty.
