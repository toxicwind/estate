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

## MCP tools (browserless-mcp 1.2.0, `src/persistent.ts`)

`persistent_status`, `persistent_navigate`, `persistent_screenshot`,
`persistent_click`, `persistent_fill`, `persistent_text`,
`persistent_evaluate`. They attach via `chromium.connectOverCDP` to the
keeper and need no `initialize_browserless`.

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
`BROWSER_KEEPER_STATUS`). E2E-verified 2026-09-21: 22 tools listed, all 7
`persistent_*` present, `persistent_status` -> `cdpAlive: true` against the
live keeper, `persistent_evaluate` round-tripped the keeper Chromium
userAgent (Chrome/148).

## Quickshell bar button

Canonical snippet: `../quickshell/BrowserToggle.snippet.qml`. Installed into
`~/.config/quickshell/ii/modules/ii/bar/UtilButtons.qml` (RowLayout tail).
Quickshell reloads the config live.
