# browser-keeper

One persistent headed Chromium for the whole mesh. First-class citizen of
browserless-mcp: MCP tasks drive it through `persistent_*` tools instead of
spawning ephemeral sessions, so logins, tabs and state survive across tasks.

## Layout

- `keeper.js` - the daemon. Owns `/home/toxic/.browserless/profiles/nv-audit`
  exclusively, exposes CDP on `127.0.0.1:9223`, writes
  `/home/toxic/.browserless/keeper/status.json`, relaunches Chromium if it
  dies. Single-instance: exits if CDP already answers.
- `keeper.sh` - pitchfork launcher (sets Wayland env, execs keeper.js).
- `pitchfork.fragment.toml` - merge into `[daemons.browser-keeper]` in
  `/home/toxic/sovereign/pitchfork.toml` (owned sequence from
  `/home/toxic/sovereign`).
- `browser-toggle.sh` - show/hide the keeper window via the Hyprland
  scratchpad (`special:browser`). Wired to the Quickshell bar button; also
  runnable by hand.

## MCP tools (browserless-mcp 1.3.0, `src/persistent.ts`)

Eleven `[keeper-first]` tools. They attach via `chromium.connectOverCDP`
to the keeper and need no `initialize_browserless`. Every argument is
zod-validated; failures throw `KeeperError` with a machine-readable code
(`TAB_NOT_FOUND`, `TAB_LAST_TAB`, `INVALID_ARGS`, `NAV_TIMEOUT`,
`SELECTOR_TIMEOUT`, `CDP_CONNECT_FAILED`, …) — nothing fails silently.

- `persistent_status` — keeper status file + CDP liveness probe (never throws).
- `persistent_tabs` — list tabs: index, URL, title, which is active.
- `persistent_new_tab [url]` — open a tab (optionally to a URL), make it active.
- `persistent_close_tab <tab>` — close by index; refuses the last tab.
- `persistent_activate_tab <tab>` — bring a tab to front.
- `persistent_navigate <url> [tab]` — per-op timeout (default 60s).
- `persistent_screenshot [fullPage] [tab]`
- `persistent_click <selector> [tab]`
- `persistent_fill <selector> <text> [tab]`
- `persistent_text [tab]`
- `persistent_evaluate <js> [tab]`

Tab ops default to the last-active tab and never touch another tab
implicitly. CDP disconnects are detected (version probe + `disconnected`
event) and reconnected with backoff + jitter. The MCP server refuses to
start when the keeper is down (fail loud; `BROWSER_MCP_ALLOW_NO_KEEPER=1`
bypasses for maintenance) and shuts down gracefully on SIGTERM/SIGINT.

## MCP serve path (how clients reach the keeper tools)

The repo MCP server is a **stdio** server — no port, no daemon. Build once,
launch per client session:

```bash
cd projects/mesh/browserless
npm install && npm run build   # tsc -> dist/ (dist/ and node_modules/ are gitignored build artifacts)
./mcp.sh                        # exec node dist/index.js on stdio
```

Registered in the mesh MCP registry
(`/home/toxic/projects/my-ai-tools/configs/mcp-registry.json`) as
`browserless-mcp` -> command
`/home/toxic/sovereign/projects/mesh/browserless/mcp.sh`.
The `persistent_*` tools attach to the keeper CDP at `127.0.0.1:9223`
(override: `BROWSER_KEEPER_CDP`); keeper state file
`/home/toxic/.browserless/keeper/status.json` (override:
`BROWSER_KEEPER_STATUS`). E2E-verified 2026-09-21: 26 tools listed
(11 `persistent_*`, first in the list), `persistent_status` ->
`cdpAlive: true` against the live keeper, and `npm test`
(`smoke/keeper-smoke.mjs`) passes against the live keeper in a scratch
tab: status → tabs → new_tab → activate → navigate → evaluate →
pageText → screenshot → error codes → close_tab → status.

## Keeper status.json

`/home/toxic/.browserless/keeper/status.json` carries: `cdp`, `pid`,
`state` (`up`/`relaunching`), `profile`, `started_at`, `relaunch_count`,
`last_error`, `at`. Relaunches back off with jitter (5s → 120s cap); a
sustained healthy run (>2min) resets the backoff. One heartbeat log line
per ~5min while healthy — no log spam.

## Quickshell bar button

Canonical snippet: `../quickshell/BrowserToggle.snippet.qml`. Installed into
`~/.config/quickshell/ii/modules/ii/bar/UtilButtons.qml` (RowLayout tail).
Quickshell reloads the config live.
