# 2026-11-02 — mosaic/flotilla merge, ghas transport, key-leak hardening (retro dossier)

Session ran the full arc: hijack discovery → product merges → transport debug →
secret-leak hardening. Every item live-verified; the charter's "contract test
before trusting a fix" held all session.

## Anomaly 101 — ghas stdio bare-invocation crash
**Symptom**: gateway tool calls to ghas → `transport error: unexpected content type: ` (empty).
**Root cause chain (three layers deep):**
1. The deployed `ghas-mcp` compiled binary was 22 days stale (Oct 9) — anomaly #73 class.
2. `server.ts` defaulted `--mode http` → bare stdio invocation threw
   `GHAS_MCP_PORT required` → process died with EMPTY stdout → mcpproxy read an empty
   response body → "unexpected content type: ".
3. The gateway's cached transport state survived per-server restarts; only a full
   thresher gateway restart cleared it.
**Fix**: tty-based mode default (stdio when piped — committed `12f68ef`), rebuild +
redeploy binary, wrapper passes `--mode stdio`, full gateway restart.
**Contract test**: direct stdio init + tools/call returns valid JSON; gateway
`ghas_health` returns full payload with `blackbird_session: true`.

## Anomaly 102 — Bun $ streams secrets to stdout
**Symptom**: `'hyi-u5H98…'` printed as the first line of `den-call` output — a LIVE
API key on the terminal.
**Root cause**: Bun `$` template-shell STREAMS child stdout to the parent's stdout by
default; `secretsmith env | grep …` inside `$` printed the key. `.quiet()` is NOT
available on the awaited promise in Bun 1.4.4-canary (`quiet is not a function`) —
the "fix" crashed the script, leak persisted. Secondary bug: the audit script used
the same `$` pattern and PASSED its own 6/6 checks while leaking (its leak-check
compared against the raw token, missing the single-quoted echo form).
**Fix**: `Bun.spawnSync` (captures, never streams) for every secret fetch — in
`den-call`, `scrub-audit.ts`, and codified in the eval prelude as
`keyringSync`/`redact`/`assertClean` (estate `fee7da271a`).
**Contract test**: `scrub-audit.ts` — 6 live-traffic scenarios, all-clean assertion on
output bytes; now leaks zero itself (fixed fetch). Verified 6/6 + keyring-path direct
run starts at `{`.

## Anomaly 103 — cross-display WM ops flicker the human's keyboard
**Symptom**: keyboard "blinking" + Termius terminal rescrolling while mosaic's
display commands ran.
**Root cause**: every adb shell command touching WindowManager serializes through the
GLOBAL WM lock shared with the IME client on display 0; each command triggers
`performSurfacePlacement` → focus re-evaluation → `mCurrentFocus=null` for 1-2
frames → IME served-view detach/rebind → visible flicker + terminal re-layout.
**Fix**: `buildShellBatch` (one adb transaction per op group), `wmGate` (800ms
min interval — IME rebinds faster), `safeWmOp` (defer while `mServedView != null`,
i.e. human actively typing) — wired into all desktop tools (mosaic-mcp).
**Contract test**: batch.test.ts + 51-test suite green.

## Anomaly 104 — vendored @opentui/solid unlinked (kappa TUI crash)
**Symptom**: kappa TUI: `TypeError: The superclass is not a constructor` at
`slot.ts:18` (SlotBaseRenderable extends BaseRenderable).
**Root cause**: `node_modules/@opentui/` contained only `core` — the `solid`
workspace symlink was missing, so kappa's module graph resolved solid through a
stale partial link whose core binding was uninitialized (TDZ on the class base).
**Fix**: `ln -s packages/vendor/@opentui/solid node_modules/@opentui/solid` —
TUI loads past module init (exits 0 headless). Durable fix for kappa: `bun
install` regenerates workspace links; the vendored solid package also needs
`react` declared for its JSX runtime.

## The domain hijack (P0 — still open, human-gated)
galleryeffusion.com (ours, NameCheap 2023, Cloudflare NS) 301s to femboy.pp.ua.
Chain verified: origin 172.96.160.178 serves effusionlabs.com 200 but 404s
galleryeffusion (tunnel config has no galleryeffusion ingress); CF edge holds the
301; all keyring CF API tokens are invalid (9109 — leaked→disabled, anomaly #84
family). Recovery = CF dashboard login (floated Firefox on the Pixel's desktop
display, Google "Last used" one tap away) → rotate tokens → delete the 301 rule →
add tunnel ingress. Every non-human step done; blocked on the login tap.

## Product moves (all committed)
- **mosaic absorbs flotilla** (architect decree: "merge, I don't want two", "NO
  flotilla language"): mosaic-mcp = 19 tools (:25245) incl. desktop-mode suite
  (`mosaic_desktop_ensure/open_app/teardown/windowing/desks` — Android 17
  display-windowing + desks API), `mosaic_overlay_app` (app-component floats —
  BlackDex proven taskId 51834 keyboard-surviving), `pixel_mirror_display`
  (READ-ONLY any-display capture via SurfaceFlinger ids — the screencap -d
  contract: SF ids ≠ DisplayManager ids), input guard (`MOSAIC_ALLOW_INPUT=1`).
  51 tests green. flotilla dir = history-only with moved-banner.
- **netrace pen** (`pens/netrace`): netrace-cli (race matrix), netrace-surface
  (aesthetic page, tailscale-served), **blamescope** (universal git-history
  semantic analyzer on bge-m3: anomalies/clusters/semantic-blame — verified on
  tau's 211 commits), **local-bge-server** (durable 1024-dim embed lane from
  ~/models/bge-m3 — independent of the expired freeinference key).
- **CHANGELOGs**: full estate coverage (202+3 backfilled, all committed).
- **Ghost paths**: 6th instance fixed (den → products/ferret-den); 0 enabled
  servers with dead paths.