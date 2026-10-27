# skopos Desktop — the headed browser + :99 agent desktop (2026-10-24)

Consolidated runbook for the skopos product: the estate's headed browser lanes
and the `:99` third-monitor agent desktop. Status verified live on 2026-10-24.
Pick up future work from here; do not re-derive.

## 1. What skopos is

skopos consolidates the estate's scattered keeper/browserless work into one
Greek-codename product. It is the headed brain of the mesh:

- **The keeper** — one persistent headed Chromium (CDP `:25233`).
- **The browserless server** — a headed member of the family on `:25130`
  (REST + WS-CDP ephemeral sessions, each rendering on `:99`).
- **The MCP server** (`browserless-mcp`, skopos `src/`) — `persistent_*` keeper
  tools + browserless REST tools.
- **The CLI** (`skopos` = `bin/skopos.ts`) — `daemon` | `watch` | `failover` | `open` | `status`.

Product home: `pens/olympus/products/skopos`. The retired CJS copies
(`ranch/keeper`, `keeper.cjs`) are gone; the product owns its entrypoints.

## 2. The :99 third-monitor agent desktop

`DISPLAY :99` is a real WM-managed desktop, not a bare Chromium:

| Layer           | Detail                                                                      |
| --------------- | --------------------------------------------------------------------------- |
| `agent-display` | Xvnc `:99`, RFB `127.0.0.1:5900` (loopback)                                 |
| `agent-wm`      | openbox from `~/.browserless/keeper/openbox-build/bin/openbox`              |
| `agent-viewer`  | noVNC websockify on `127.0.0.1:6080` (loopback, **interactive**)            |
| `tint2`         | the taskbar (floaty dock); `~/.config/tint2/tint2rc` (panel 100%×30 bottom) |
| `grid-4`        | `estate/bin/grid-4` — 2×2 tiling (`PANEL_H=30` = tint2 height)              |

`wmctrl -m` → `Name: Openbox`; the desktop hosts the keeper Chrome, the kappa
TUI, and any apps spawned via `skopos open`. The viewer is interactive
(`view_only=false`), so the human can click/type on the agent desktop.

## 3. The four skopos daemons + their real ports

| Daemon                                               | Role                                                                                        | Port(s)                    |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------- | -------------------------- |
| `estate/skopos`                                      | keeper supervisor (headed Chromium)                                                         | CDP `25233`, ready `25236` |
| `estate/skopos-failover`                             | on-demand takeover drop-in (probes :25233, spawns chromium only if primary down past grace) | —                          |
| `estate/skopos-floaty`                               | signalhead lamp (busy/waiting/idle)                                                         | `25238`                    |
| `estate/browserless`                                 | **headed** browserless server (REST + WS-CDP sessions)                                      | `25130`                    |
| `estate/agent-display` / `agent-wm` / `agent-viewer` | the `:99` desktop stack                                                                     | `5900` / `6080`            |

Port SSOT: `estate/config/ports.env`.

## 4. Headed browserless design

The existing browserless v2 server on `:25130` is headed, not headless:

- `DISPLAY=:99` + `XDG_RUNTIME_DIR` in the daemon env (monolith + fragment), and
  `run.sh` exports them (default `:99`, overridable).
- `launch.headless=false` is the skopos default: the client (`skopos/src/client.ts`)
  injects `launch:{headless:false}` into ephemeral content/screenshot/pdf
  sessions, so they render **headed on `:99`**.
- **Dedicated profile**: `DATA_DIR` = `~/.browserless/profiles/skopos` (set in
  `run.sh`). NEVER `nv-audit` — the keeper owns that exclusively; two live
  Chromes must not share a `--user-data-dir` (Chrome profile-lock).
- Versions/verify: `curl http://127.0.0.1:25130/health` → 200.

This deliberately does NOT patch the vendored build
(`$_BLESS/app/build/browsers/browsers.playwright.js`); the per-request
`headless:false` is the config-friendly path the build already supports.

## 5. The skopos CLI

```bash
bun pens/olympus/products/skopos/bin/skopos.ts status   # keeper + floaty summary
bun pens/olympus/products/skopos/bin/skopos.ts open xmessage   # launch in the floaty
bun pens/olympus/products/skopos/bin/skopos.ts watch    # hot-reload the keeper (dev)
bun pens/olympus/products/skopos/bin/skopos.ts daemon   # run the keeper supervisor
bun pens/olympus/products/skopos/bin/skopos.ts failover # takeover drop-in
```

`estate/bin/keeper-open` now **delegates** to `skopos open` (one implementation).
`skopos open` pins `DISPLAY=:99`, setsid-detaches, pings the floaty lamp
(`/set/busy` → signalhead `:25238`), and lists `:99` windows.

`estate/bin/keeper-open <command...>` still works unchanged for legacy hooks.

## 6. Cookie persistence (kept from the older runbook)

The full Google session injects (15/15) and persists to disk in the keeper's
`nv-audit` profile (`Default/Cookies` holds real encrypted blobs), surviving a
full keeper restart. `secretsmith chromium-cookies` may report `decrypted:false
/vlen 0` — that is os_crypt key mismatch, NOT data loss; do not chase it.

## 7. Re-auth essentials (real ports)

Real keeper CDP: **`http://127.0.0.1:25233`** (SSOT `config/ports.env`).
Throwaway `:9223` chrome-for-testing is NOT the keeper — never point tools at it.
To re-auth the keeper: inject the full auth cookie set via the keeper CDP
(`PUT http://127.0.0.1:25233/json/new?<url>` keeps the real profile).

## 8. Known stale references (do not copy)

- `:9223` / `:25154` anywhere — replaced by `:25233`.
- `ranch/keeper` / `keeper.cjs` / `browser-keeper` daemon name — retired in
  favour of `olympus/skopos` and the `estate/skopos*` daemons.
