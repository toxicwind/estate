---
name: exa
description: "Use Exa when the user asks for Exa, neural web search, or this provider's API."
---

# Exa

## Purpose
Exa AI search (neural web search) with the user-connected `custom.exa`
credential. Four agent tools: search, contents, find-similar, answer.

## Tooling
```sh
exa.mjs search <query> [--n N] [--type auto|neural|keyword] [--livecrawl always|fallback|never] [--chars N]
exa.mjs contents <url>... [--chars N]
exa.mjs find-similar <url> [--n N]
exa.mjs answer <query>
```
Output is JSON on stdout. Every call is appended to
`~/.cache/shingle/exa_calls.jsonl` (endpoint, elapsed_ms, ok, cost_usd) for
cost tracking. Exit 2 is a usage error, exit 3 a credential error.

## Credential resolution
Two sources, in order, and the second only when the first is *absent*:

1. **authd broker** at `/run/hatch/auth/authd.sock` returns an `hsurr:*`
   surrogate that the egress proxy swaps for the real key. The helper never
   sees the real value.
2. **secretsmith** resolves the key from the local `KEY=value` store when the
   broker socket is missing — which is the case on this box. Only a genuinely
   absent socket triggers this; a broker that answers with an error surfaces
   that error rather than silently switching credential sources.

Both paths keep the real value out of chat, argv, logs, and the call log.
`SECRETSMITH` overrides the secretsmith binary; `JARVIS_AUTHD_SOCK` overrides
the socket.

## Auth
The credential is already stored; nothing here collects one. Resolve auth
through the sources above — credential values never enter chat, secret
environment variables, secret flags, or auth files. Authenticated requests go
only to `api.exa.ai`; the allowlist is checked before any credential is
resolved, so a rogue host never causes a secret to be read at all.

A 401 or 403 is a question about the request before it is a question about
the key. Check that the credential was attached at all: a request built
without the helpers carries nothing, and that looks exactly like a wrong or
under-scoped token. Only once a request that did carry the credential is
still rejected, call `credentials.request_api_access` with `reconnect` to
replace it. The connector is stored as `custom.exa`.

## Operating Rules
1. Use this skill when the user asks for Exa or neural web search.
2. Restrict authenticated requests to: api.exa.ai.
3. Do not print, log, or persist raw credentials.
4. If auth is missing or rejected, follow the Auth section rather than asking for a key.
5. Note: yote (the bridge box) has no credential broker — the vault
   credential only works from this cell. Yote's `awrawr_mcp.py` carries
   `exa_*` tools too, but they need a key file provisioned operator-side at
   `~/.config/exa/api_key` (mode 600).