# context7

Context7 live documentation lookup: resolve a library name to a Context7 library ID, then fetch up-to-date docs and code snippets. Triggers on: library docs, Context7 lookup.

&larr; **Back to top** <!-- for-the-badge alignment -->

## Hero

Resolves a library name to a Context7 library ID, then returns up-to-date documentation and code snippets for that library. Use whenever you need current docs for a dependency instead of relying on training knowledge — ensures you're always working with the latest, not stale cached information.

## What It Does

- **Search step**: Resolves a library name to a library ID via `https://context7.com/api/v2/search?query=<query>` with `Authorization: Bearer $CONTEXT7_API_KEY`
- **Context step**: Fetches documentation chunks relevant to specific queries via `https://context7.com/api/v2/context?libraryId=<id>&query=<query>&type=txt`
- **Liveness check**: Quick check to confirm `CONTEXT7_API_KEY` is set and the API is reachable (expect HTTP 200 on ping endpoint)
- **MCP alternative**: Where an MCP gateway is running, the Context7 MCP server (`@upstash/context7-mcp`) is configured with the same `${CONTEXT7_API_KEY}` env reference — value never written literally into config

## Features

| Feature | Detail |
|---|---|
| **Live docs** | Always up-to-date; never rely on training knowledge for a dependency |
| **Two-step flow** | Search → resolve library ID → fetch context/docs |
| **Query flexibility** | Multiple queries can be passed (e.g. `hooks`, `useEffect`) |
| **Output format** | Plain text documentation chunks relevant to the query |
| **MCP compatible** | Same `CONTEXT7_API_KEY` env var works with MCP gateway configs |
| **Liveness verification** | Ping endpoint confirms key and API availability |

## Quick Start

```bash
# 1. Ensure CONTEXT7_API_KEY is sourced (from ~/.bashrc, yote .secrets, or vault)
source ~/.bashrc

# 2. Search for a library and get its ID
curl -s -H "Authorization: Bearer $CONTEXT7_API_KEY" \
  "https://context7.com/api/v2/search?query=react%20hooks" | head -c 2000

# 3. Fetch docs for the library ID (URL-encode leading slash as %2F if needed)
curl -s -H "Authorization: Bearer $CONTEXT7_API_KEY" \
  "https://context7.com/api/v2/context?libraryId=%2Ffacebook/react&query=hooks&query=useEffect&type=txt" | head -c 4000

# 4. Liveness check — expect 200
[ -n "$CONTEXT7_API_KEY" ] || { echo "CONTEXT7_API_KEY not set"; exit 1; }
curl -s -o /dev/null -w "%{http_code}\n" \
  -H "Authorization: Bearer $CONTEXT7_API_KEY" \
  "https://context7.com/api/v2/search?query=ping"
# expect: 200
```

## Config

- `CONTEXT7_API_KEY` environment variable is required — it must be sourced from:
  - yote `/home/toxic/.secrets` (`export CONTEXT7_API_KEY=...`, mode 0600)
  - yote + hatch shell profiles (`~/.bashrc`)
  - yote OpenFang vault (`openfang vault list` shows the name; values hidden)
  - MCP gateway configs reference it as `${CONTEXT7_API_KEY}` (env expansion)
- The value is never written literally into configs or logs — always read from env
- Agents must source it (`source ~/.bashrc`, or read it from `.secrets` / the vault) — never paste a key value into code, configs, logs, or chat

## Contributing

Use this skill whenever you need current docs for a dependency instead of relying on training knowledge. Read the key from the environment, never hardcode it. Where an MCP gateway is running, the Context7 MCP server uses the same env variable reference.

## License

Open Claw — see `skill.toml` for details.

## Security

- **Never hardcode** `CONTEXT7_API_KEY` in code, configs, logs, or chat
- The API key lives in protected locations only: `/home/toxic/.secrets` (mode 0600), vault, or hatch shell profiles
- Agents must source the key — do not paste key values into chat or command arguments
- MCP gateway configs reference it as `${CONTEXT7_API_KEY}` — env expansion only; value never written literally
- If `CONTEXT7_API_KEY` is not set, the liveness check will fail (exit 1)