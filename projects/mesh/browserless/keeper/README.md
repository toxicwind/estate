# browser-keeper

One persistent headed Chromium for the whole mesh. First-class citizen of
browserless-mcp: MCP tasks drive it through `persistent_*` tools instead of
spawning ephemeral sessions, so logins, tabs and state survive across tasks.

## Layout

- `keeper.js` - the daemon. Owns `/home/toxic/.browserless/profiles/nv-audit`
  exclusively, exposes CDP on `127.0.0.1:9223`, writes
  `/home/toxic/.browserless/keeper/status.json`, relaunches Chromium if it
  dies. Single-instance: exits if CDP already answers.
- `keeper.sh` - pitchfork launcher for the isolated display: unsets `WAYLAND_DISPLAY`, sets `DISPLAY=:99`, execs keeper.js (Forge 2026-09-21 — the keeper never renders in Chris's Hyprland session).
- `pitchfork.fragment.toml` - merge into `[daemons.browser-keeper]` in
  `/home/toxic/sovereign/pitchfork.toml` (owned sequence from
  `/home/toxic/sovereign`).
- `browser-toggle.sh` - LEGACY: showed/hid the keeper window via the Hyprland
  scratchpad. Dead since the keeper moved to the isolated Xvnc :99 display
  (no Hyprland window exists any more); kept for reference.

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

## Agent display + interactive viewer (Forge 2026-09-21)

The keeper Chromium renders on an **isolated virtual display** — never in
Chris's Hyprland session. (Root cause of the 2026-09-21 takeover: keeper.sh
exported `WAYLAND_DISPLAY=wayland-1`, so agent windows stole his mouse and
focus.)

- `agent-display` — `Xvnc :99`, RFB on `127.0.0.1:5900` only (`-localhost`),
  VNC password auth via `/home/toxic/.browserless/vncpasswd` (0600, Chris's —
  never rotated, never stored anywhere else).
- `agent-viewer` — websockify serving stock noVNC on **`127.0.0.1:6080`
  (loopback-only)**. The viewer is **INTERACTIVE**: noVNC defaults
  `view_only=false` (verified in vendored `app/ui.js`; `mandatory.json` and
  `defaults.json` are empty), so Chris can click, type, and take over the
  agent browser. View-only was explicitly rejected (Chris 2026-09-21:
  "view only is no point, user should be able to interact or help lol").
- External route (2026-09-21, Forge): tailnet-only via `tailscale serve`
  on `:8443` -- `/agent-browser` -> `127.0.0.1:6080` (declared in
  `projects/yote/ops/funnel-map.sh` SERVE_MAP). No funnel, no token gate
  (Chris 2026-09-21: token gate was not wanted -- tailscale and network and
  agent access only). The old gate (`../viewer/agent-viewer-gate.py`, was
  `:6081`) is retired, kept as reference only. noVNC resolves its
  `./websockify` WS path relative to the page URL, so the subpath mount just
  works. Use the MagicDNS name -- raw tailnet IPs fail the TLS handshake
  (SNI).
- VNC auth is untouched: noVNC still prompts for the Xvnc password.

Viewer URL: `https://github-mcp-host.tailc9ac71.ts.net:8443/agent-browser/vnc.html`

Restart/rollback: `pitchfork-restart agent-viewer --reregister` (picks up
`pitchfork.toml` run-line changes).
To close the external route without touching the daemons:
`tailscale serve --https=8443 --set-path /agent-browser off` as root.
