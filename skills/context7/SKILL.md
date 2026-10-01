---
name: context7
description: >
  Context7 live documentation lookup: resolve a library name to a Context7 library ID, then fetch up-to-date docs and code snippets. Triggers on: library docs, Context7 lookup.
---

# context7 skill (ember)

Context7 is a live documentation lookup service: it resolves a library name
to a Context7 library ID, then returns up-to-date docs/code snippets for that
library. Use it whenever you need current docs for a dependency instead of
relying on training knowledge.

## Auth — read the key from the environment, never hardcode it

The API key lives in the `CONTEXT7_API_KEY` environment variable. It is
installed in:

- yote `/home/toxic/.secrets` (`export CONTEXT7_API_KEY=...`, mode 0600)
- yote + hatch shell profiles (`~/.bashrc`)
- yote OpenFang vault (`openfang vault list` shows the name; values hidden)
- MCP gateway configs reference it as `${CONTEXT7_API_KEY}` (env expansion)

Agents must source it (`source ~/.bashrc`, or read it from `.secrets` /
the vault) — never paste a key value into code, configs, logs, or chat.

## v2 REST endpoints

Base: `https://context7.com`

### 1. Search — resolve a library name to a library ID

```bash
curl -s -H "Authorization: Bearer $CONTEXT7_API_KEY" \
  "https://context7.com/api/v2/search?query=react%20hooks" | head -c 2000
```

Response shape (JSON): `{ "results": [ { "id": "/facebook/react", "title": ...,
"description": ..., "branch": ..., "lastUpdateDate": ..., "state": ...,
"totalSnippets": ..., "totalTokens": ..., "trustScore": ... }, ... ] }`.
Pick the `id` of the best match for step 2.

### 2. Context — fetch docs for a library

```bash
curl -s -H "Authorization: Bearer $CONTEXT7_API_KEY" \
  "https://context7.com/api/v2/context?libraryId=/facebook/react&query=hooks&query=useEffect&type=txt" | head -c 4000
```

Response shape: plain text (`type=txt`) documentation chunks relevant to
`query`. `libraryId` is the `id` from the search step (URL-encode the
leading slash as `%2F` if your client needs it).

## Quick liveness check

```bash
[ -n "$CONTEXT7_API_KEY" ] || { echo "CONTEXT7_API_KEY not set"; exit 1; }
curl -s -o /dev/null -w "%{http_code}\n" \
  -H "Authorization: Bearer $CONTEXT7_API_KEY" \
  "https://context7.com/api/v2/search?query=ping"
# expect: 200
```

## MCP alternative

Where an MCP gateway is running, the Context7 MCP server
(`@upstash/context7-mcp`) is configured with the key passed as the
`${CONTEXT7_API_KEY}` env reference — same variable, same rule: the value
is never written literally into the config.