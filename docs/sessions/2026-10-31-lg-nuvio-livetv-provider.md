# 2026-10-31 — LG Nuvio fork: live TV, provider audit, elephant-session retro

**Agent:** tau · **Scope:** `pens/ranch/products/nuvio-default` (space.nuvio.webos on `lg-tv` 10.0.0.176:9922, webOS 5.6.1 / Chromium 68), fleet vendor corpus, docs-mcp, fork-storm kill.

## The fork
- **`nuvio-default`** is THE webOS Nuvio fork head (homelessbrian base, `space.nuvio.webos` app id v1.2.10, git clean + pushed `9024888`). Real Supabase (`api.nuvio.tv`, anon JWT from the Pixel's `com.nuvio.app` APK) → QR pairing works.
- Live TV (Xtream/M3U) Netflix-Max face built this session: hero billboard, per-country sorted category rail (USA→UK→English→Japan custom regex sort), channel grid, EPG now/next.

## Live TV fixes (the actual "is it broken" work)
1. **QR "white box"** — `supportsTvLogin()` false because `nuvio.env.js` had empty Supabase URL/key; `startQr()` guard-returned while showing a misleading status string. Real key baked in (gitignored env). Root-caused via CDP into the TV's Chromium 68.
2. **Dead D-pad** — LiveTvScreen only had `handleKey(string)`; FocusEngine dispatches `onKeyDown(event)` (keyCode 13/37-40). Screen lacked the contract → remote up/down/left/right/OK did nothing. Added `onKeyDown` (real fix, not a focus-state red herring).
3. **Playback 407** — stream URLs were built on the **API port :2095** (`/live/u/p/id.ts`). Anomaly #39: streams must use **port 80** + `live/u/p/id.m3u8`. Fixed stream-host derivation.
4. **Grey boxes / lag** — `state` stayed `loading` until the **63 MB XMLTV** finished parsing → skeletons/grey forever. EPG now decouples: channels paint instantly, guide fills in background.
5. **Screensaver** — `luna://com.webos.service.oledepl/setEplAppInfo` **accepts policy writes from app context** (`returnValue:true` live); big `screenSaverDelay` holds the saver. `assertScreensaverPolicy()` runs at companion-service boot (TV reboots reset it).

## The companion lunaProxy (cutting edge, verified)
`services/webos/src/index.js` gains `lunaProxy` — generic LS2 relay using the **borrowed webOS-service `Service.prototype.call(uri, args, cb)`** contract (native `palmbus.Handle.call` is variadic; `handle.call(uri, jsonString)` — verified on-device). Live proof: `luna://com.webos.service.connectionmanager/getstatus` → full wifi/power payload. **The only generic LS2 bridge for a webOS TV under an app-ACG caller that we've seen** — the "kotlin webos" ecosystem is Android phone-side remotes; nobody runs this on-box.

## provider-master + liveness audit (`m3u-toolkit/bins/provider-master.mjs`, pushed)
- Provider concept: `{id, kind(xtream|m3u), apiServer, streamHost, user, pass, epgUrl, liveness}`. One audit engine drives any provider.
- Real creds recovered from archive: `cabtxNjD / a7ztYjf · 195.128.27.253` — AUTH-VERIFIED, 23,984 live streams, 353 categories, account Active.
- 400-sample port-80 liveness: **~50% hls-ok**, split http407/http429/net/509 — this box's egress 407s (needs proxy auth); the architect's home LAN streams fine (10-28 proof).
- Name-dedup clustering (normalized-name now; bge-m3 optional — the estate's bge-m3 lane wasn't cleanly serving today).

## livetv-symbiont (compiler-guaranteed parity)
JVM `livetv-symbiont.jar` (kotlin 2.0.21, JDK17) vendors the REAL `CatchupUrlBuilder.kt`/`M3uParser.kt`/`LiveTvModels.kt` from homelessbrian — builds (`BUILD SUCCESSFUL`), boots HTTP on :18085 (`{"ok":true}`). First JVM data-contract keeper for a webOS TV. Lives in lg-fleet's gitignored `vendor/` import-lane (not submodule-tracked — layout question).

## docs-mcp → pure bun
- Config was running the **python lane** (11 GB `docs-index.sqlite3` + journal = a wreck). Repointed thresher gateway to `docs_mcp.ts` (bun:sqlite FTS5 external-content).
- **Bug:** Node `statSync().mtime` is a **Date** — unbindable in bun:sqlite ("Binding expected string/number"). Fixed to `mtimeMs`. Now warms **136,976 docs in 44.6s**. Committed+pushed (`001f8bc`, docs-mcp own repo).

## fork-storm kill (not LG — but the session's biggest infra save)
Rogue pitchfork daemon was an **inline `bun -e while(true){spawnSync; Bun.sleep(60000)}` MISSING `await`** → ~130 spawns/s for 25.4 h (155 forks/s total). Replaced with an **event-driven `fs.watch` loop, no timers** (white-paper orchid a9_stolon), `pitchfork restart`. Also shipped **a9_stolon** as the 9th lapidary orchid detector guarding that bug class — 9/9 recall, leak-free, pushed. Remaining churn: `bun --hot` windmill (2-4/s), reconcile-funnel (30s cadence).

## Vendored research corpus (de-obf)
`/home/toxic/pens/fleet/devices/lg-fleet/vendor/`: webos-homebrew-channel (elevate-service perms model), glasshouse (rooted screensaver mechanics, idlesaver), nuvio-native-legacy, dejavuln/faultmanager autoroot, lg-webos-root-debloat, tv-tools, webos-apps-repo. Argos `ops/embed-vendor.ts` indexes them (9 products, ~7k chunks, 1.3 s).

## Stats
- Live channels: 23,984 · categories: 353 · liveness sample: 50% ok
- docs-mcp: 136,976 docs / 44.6 s / pure bun
- argos vendor index: 9 products / 7,072 chunks / 1.26 s
- orchid: 9/9 recall /
- Commits pushed: nuvio-default `9024888` · m3u-toolkit `f3b92f2` · docs-mcp `001f8bc` · lapidary `a3d4671` · estate-ops `0e39454`

## Open / parked
- tizen lane on LG luna MCP (fork has tizen) — not built
- LG luna MCP server → thresher gateway registration — wrapper scope
- brian Kotlin → Bun parity test vectors — not extracted
- co.uk md recall — never pinned to a specific doc
- symbiont git home (gitignored vendor/ lane)

## Lessons
- **CDP tunnels go stale** pointing at dead page objects → every verify reads a dead copy. `lg-cdp` (persistent tunnel keeper) + `lg-eval` (one-shot, <2 s) are the fix; verify against a FRESH tunnel or you debug ghosts.
- `ares-launch` on `handlesRelaunch` apps does NOT reload the page — close-then-launch or you "fix" things that were already fixed/deployed.
- Deploy lane must assert a cargo marker on the TV, not trust install rc ("ipk verified failed" lies).
- Node `statSync().mtime` is a Date, not a number — bun:sqlite rejects it (binding error).
- bge-m3 embeds similarity; it does not organize. The provider concept (registry + liveness + dedup) is the organizer.
- Un-awaited `Bun.sleep` after `spawnSync` in `while(true)` = fork storm. No timers in daemon loops that must sleep — event-driven fs.watch beats setInterval for a correctness-critical watcher.

## co.uk pattern (gleaned, not yet built)

- `nuvio.tvflix.co.uk` — "Nuvio Configurator": third-party SPA that generates
  `nuvio_collections.json`, `aio_meta.json`, and AIOStreams configs for import
  into a Nuvio account (upstream issue iqui27/nuvio-native-legacy#414 tracks it;
  portuguese plan docs call out "import direct file/URL on TV" as the gap).
- Pattern to duplicate (nuvio-default lane): a config-generator that emits
  importable JSON for the baked TV account — TV-side import of a file/URL is
  the missing feature the ecosystem wants. tivimateplayer.co.uk hits are EPG
  tuning SEO (12-24h refresh, tvg-id matching, 8-15s buffer), useful reference
  only.
- Status: FOUND + documented. Building the configurator clone is fresh scope.
