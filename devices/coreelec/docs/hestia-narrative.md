# HESTIA — the narrative (what she actually does)

> Hestia (Ἑστία) is the Greek goddess of the hearth — the sacred fire at the
> center of the home that never goes out. In the estate, **hestia** is the
> living-room reference CoreELEC box (10.0.0.246): the hearth fire that the
> whole home-theater A/V stack gathers around, and the canonical "it has
> correct" source of truth for the Kodi fleet.

## What hestia actually DOES

Hestia is not just a name — she performs a concrete role in the estate. Her
job, end to end:

1. **Is the hearth of the home theater.** HDMI out → **Marantz AVR** (EDID
   "marantz-AVR"). She is the audio passthrough master: AC3 / DTS / TrueHD /
   DTS-HD bitstream to the AVR for the living-room speakers. The AVR is her
   hearth — she feeds it the fire.

2. **Is the CEC master of the theater.** She drives the Marantz over the
   kernel AOCEC bus (`cec-scan` / `cec-power` / `cec-key` via coreelec-mcp).
   CEC is locked down (2026-11-05) so she never triggers a TV/AVR shutdown —
   the hearth fire stays lit.

3. **Is the reference source of truth.** "It has correct." Settings and
   playback dupe 246 → 225 (athena), except tv/audio which stay per-box.
   When a setting is right, hestia is where it was proven.

4. **Runs the eternal fork** — the kodi-fleet fork of the Redlight addon
   (`plugin.video.eternal`, v2.6.7, 100% redlight + lasso purged 2026-11-05).
   This is her scraper engine: AllDebrid/Offcloud/Premiumize/Real-Debrid/TorBox +
   AIOStreams + EasyNews/NZB + Trakt/PunchPlay/Simkl/MDBList. She resolves and
   plays streams via `coreelec-mcp play-tmdb`.

5. **Is the playback engine.** `coreelec-mcp` (`@geode/coreelec-mcp`, bun,
   deps `@modelcontextprotocol/sdk` + `zod`) drives her over JSON-RPC
   `http://10.0.0.246:25270/jsonrpc`. `play-tmdb` injects `autoplay=true` so
   she auto-picks the best source without a UI lockup.

6. **Is the fleet handoff origin.** `kodi-handoff` transfers playback between
   hestia and athena — the flame passes from one hearth to the other.

7. **Is the port SSOT anchor.** Her ports live in the estate 25xxx range:
   `HESTIA_RPC_PORT=25270`, `HESTIA_SLYGUY_PORT=25272` (config/ports.env).

## Hardware (the vessel)

- Amlogic **S905X3** (`sm1_s905x3_4g_1gbit`), 4×Cortex-A55, 3.8G RAM, kernel
  4.9.269 aarch64.
- Audio: ALSA **`AML-AUGESOUND`** card, HDMI on `hdmi:CARD=AMLAUGESOUND,DEV=0`.
- Net: wlan0 only. SSH `root:coreelec` (POSIX sh). Storage 52.6G, 5% used.
- Skin: Fen-tastic. 56 addons. armhf userland (no bun/FFS on-box).

## The lock (2026-11-05 session)

- **PulseAudio killed** → kodi opens `CAESinkALSA hdmi:...DEV=0`, 0 sync errors.
- **Correct TMDB id 97** (not 31147="I-Techie") + `autoplay=true` → playback works.
- **Single kodi.bin** (stale 2nd instance holding slyguy 8095 caused SIGSEGV).
- **Ports** 8080→25270, 8095→25272.
- **CEC locked** (was triggering shutdown).
- **eternal fork 100% redlight + lasso purged** (207+14+219 edits, redlight.py→lasso.py→eternal.py, addon id plugin.video.eternal).

## Open (the fire still needs tending)

- Eternal spawns 6 monitor services at boot (menu-latency tax).
- Dead scrapers (Knaben 403, Sootio/WebStreamr/yastream timeouts) stall resolve.
- True bitstream passthrough to Marantz not yet verified (currently PCM S16NE).
- Faster play via code-race + hepapistos rig agent per phase.

## Identity

- **hestia** = 10.0.0.246, living-room reference CoreELEC box.
- **athena** (proposed) = 10.0.0.225, bedroom Android-TV Kodi APK.
- Docs: `devices/coreelec/docs/recon-and-codename.md`, `box-inventory.md`,
  `menu-latency.md`; `docs/anomalies/2026-11-05/*`.