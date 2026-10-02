# exa

Exa AI search (neural web search) with the user-connected `custom.exa` credential. Four agent tools: search, contents, find-similar, answer.

&larr; **Back to top** <!-- for-the-badge alignment -->

## Hero

Provides neural web search capabilities through the Exa API, with four tool endpoints (search, contents, find-similar, answer) and automatic cost tracking. When the user asks for Exa or neural web search, this skill routes the request through the proper auth flow and returns JSON output on stdout.

## What It Does

- **Four tool endpoints**: `exa.mjs search`, `exa.mjs contents`, `exa.mjs find-similar`, `exa.mjs answer`
- **Output format**: JSON on stdout, appended to `~/.cache/shingle/exa_calls.jsonl` for cost tracking (endpoint, elapsed_ms, ok, cost_usd)
- **Credential resolution**: Two sources in order: (1) authd broker at `/run/hatch/auth/authd.sock` returns `hsurr:*` surrogate, (2) secretsmith resolves key from local `KEY=value` store — only triggered when the broker socket is absent
- **Auth strictness**: Real credential values never enter chat, argv, logs, or the call log; only `hsurr:*` surrogates are sent, and only to `api.exa.ai`
- **Error handling**: Exit 2 = usage error, exit 3 = credential error; 401/403 checks request before key
- **Yote bridge note**: Yote has no credential broker — the vault credential only works from this cell; yote's `awrawr_mcp.py` carries `exa_*` tools but needs a key file at `~/.config/exa/api_key` (mode 600)

## Features

| Feature | Detail |
|---|---|
| **Four tools** | search, contents, find-similar, answer — all output JSON on stdout |
| **Cost tracking** | Every call logged to `~/.cache/shingle/exa_calls.jsonl` with endpoint, elapsed_ms, ok, cost_usd |
| **Auth sources** | authd broker (preferred) → secretsmith fallback; real key never in chat/argv/logs |
| **Credential isolation** | Only `hsurr:*` surrogates sent to egress proxy; real key never persisted |
| **Yote compatibility** | Works from this cell; yote bridge needs separate key provisioning at `~/.config/exa/api_key` |
| **Exit codes** | 0 = ok, 2 = usage error, 3 = credential error |

## Quick Start

```bash
# Search Exa neural web
exa.mjs search "neural web search patterns" --n 5 --type neural

# Get page contents
exa.mjs contents https://example.com --chars 1000

# Find similar pages
exa.mjs find-similar https://known-page.com --n 3

# Answer a question
exa.mjs answer "What are the latest trends in LLM serving?"

# With specific char limit
exa.mjs search "query" --chars 200
```

## Config

- Credential is already stored; never ask user to paste a raw key in chat
- Set `custom.exa` secret via operator-side vault/credentials system
- If auth is missing or rejected: follow the Auth section — do not ask for a key
- Environment: `custom.exa` surrogate is sent; real key never in environment variables
- Yote: key file at `~/.config/exa/api_key` (mode 600), provisioned operator-side

## Contributing

Use this skill when the user asks for Exa or neural web search. Restrict authenticated requests to `api.exa.ai`. Do not print, log, or persist raw credentials. If auth is missing or rejected, follow the Auth section rather than asking for a key.

## License

Open Claw — see `skill.toml` for details.

## Security

- Never print, log, or persist raw credentials
- A 401 or 403 is a question about the request before it is a question about the key
- Check that the credential was attached at all: a request built without the helpers carries nothing
- Only once a request that did carry the credential is still rejected should you call `credentials.request_api_access` with `reconnect`
- Authenticated requests go only to `api.exa.ai`; the allowlist is checked before any credential is resolved
- Yote bridge: `awrawr_mcp.py` carries `exa_*` tools but needs a key file at `~/.config/exa/api_key` (mode 600) — operator-side provisioning only