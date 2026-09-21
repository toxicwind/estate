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

## Quickshell bar button

Canonical snippet: `../quickshell/BrowserToggle.snippet.qml`. Installed into
`~/.config/quickshell/ii/modules/ii/bar/UtilButtons.qml` (RowLayout tail).
Quickshell reloads the config live.
