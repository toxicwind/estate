# Browserless — sovereign mesh

Browser automation for the fleet: the **browserless.io MCP server** plus the
**itvx native-launcher deployment** of the browserless server itself, unified
in one mesh project at `projects/mesh/browserless/` (visible as `mesh/browserless/`).

## What the itvx additions were

The live deployment never forked browserless code. `/home/toxic/.browserless/app`
is stock **browserless.io v2.49.0** (SSPL, npm-installed — build output and
`node_modules` are runtime artifacts, not tracked here). Everything itvx added
was the ops layer, now carried in this project:

- `server/run.sh` — native launcher: sources the token from 0600
  `/home/toxic/.browserless/.env`, binds `127.0.0.1`, port from `BROWSERLESS_PORT`
  (25130), `PLAYWRIGHT_BROWSERS_PATH=/home/toxic/.browserless/browsers`,
  `CONNECTION_TIMEOUT=60000`, `CONCURRENT=10`, `NODE_ENV=production`, then
  `exec node /home/toxic/.browserless/app/build/index.js`.
- Pitchfork daemon `[daemons.itvx-browserless]` on **:25130** (canonical section
  in `server/pitchfork.fragment.toml`; live section in
  `/home/toxic/sovereign/pitchfork.toml`). Owned restart sequence: `pitchfork stop
  itvx-browserless` → verify dead via `ss` → `pitchfork clean --daemon
  itvx-browserless` → `pitchfork start itvx-browserless` from `/home/toxic/sovereign`
  (or the `bin/pitchfork-restart` wrapper).
- `config/ports.env`: `BROWSERLESS_PORT=25130` (collision resolved 2026-09-14 —
  browserless keeps 25130).

## Token rule (non-negotiable)

The server token lives **only** in `/home/toxic/.browserless/.env` (mode 0600).
It is sourced at launch, never printed, never logged, never committed.
`server/.env.example` and `env.example` are placeholders with empty values.
`.gitignore` carries the token-scrub patterns (`*.pat`, `.env*`, `*secret*`, `*token*`).

## Layout

```text
projects/mesh/browserless/
├── src/                    # MCP server (index.ts, client.ts, simple-server.ts, types.ts)
├── server/
│   ├── run.sh              # itvx native launcher (pitchfork runs this)
│   ├── .env.example        # placeholder for the 0600 /home/toxic/.browserless/.env
│   └── pitchfork.fragment.toml  # canonical [daemons.itvx-browserless] section
├── config.json             # live endpoint: 127.0.0.1:25130 (token intentionally null)
├── env.example             # MCP client env template (live defaults)
├── Dockerfile / docker-compose.yml  # legacy docker path (native launcher is live)
├── smithery.yaml           # smithery packaging
├── ref/browserless_api_reference.md
├── test-*.js               # feature test scripts
└── TEST_RESULTS.md         # historical feature test results
```

## Running the server

```bash
# via pitchfork (canonical)
/home/toxic/sovereign/bin/pitchfork-restart itvx-browserless
# liveness (no token needed to prove it's serving — 401 means the gate is up)
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:25130/pressure
# authenticated check (token stays in this shell; only the status code leaves it)
set -a; . /home/toxic/.browserless/.env; set +a
curl -s -o /dev/null -w '%{http_code}\n' "http://127.0.0.1:25130/pressure?token=$BROWSERLESS_TOKEN"
```

## Running the MCP server

```bash
cd projects/mesh/browserless
npm ci            # or npm install
npm run build     # tsc -> dist/
# stdio MCP server, talks to the live 127.0.0.1:25130 by default
BROWSERLESS_TOKEN=... node dist/index.js
# simpler single-purpose server (env-driven URL, defaults to live endpoint)
node dist/simple-server.js
```

`initialize_browserless` defaults to host `127.0.0.1`, port `25130` — the live
mesh server. `simple-server.ts` builds its URL from `BROWSERLESS_PROTOCOL/HOST/PORT`
with the same defaults.

## Feature status

Working against the live server: content extraction (`/content`), PDF generation
(`/pdf`). Screenshot timed out under test load; `/function` needed a different
payload format; `/export` and `/performance` are not in this server build.
Details: `TEST_RESULTS.md` (historical run against the old docker endpoint;
re-run `test-all-features.js` to refresh).

## Links

- Mesh overview: `mesh/README.md`
- Fleet knowledgebase: `docs/fleet-knowledgebase.md`
- Upstream MCP project this was merged from: Lizzard-Solutions/browserless-mcp
