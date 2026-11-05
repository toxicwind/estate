# HESTIA — CoreELEC 246 device identity (maximal recon, 2026-11-05)

> **hestia** is the estate's canonical living-room CoreELEC reference box —
> the "it has correct" source of truth for the Kodi fleet. This doc is the
> full device identity: hardware, CEC, deps, fleet role, and estate integration.

## Identity

```
codename: hestia
host:     10.0.0.246
id:       246
role:     living-room reference CoreELEC (Kodi fleet source of truth)
sibling:  225 (bedroom Android-TV Kodi APK, "athena" proposed)
```

Named **Hestia** (Greek goddess of the hearth) — the home-theater hub the whole
living-room A/V stack hangs off. The estate's Greek lineage (olympus products)
extends to the device fleet: hestia is the hearth, athena (proposed) the
secondary.

## Hardware

- **SoC**: Amlogic **S905X3** (`sm1_s905x3_4g_1gbit` dt-id), 4×Cortex-A55
  (part 0xd05), 3.8G RAM, kernel 4.9.269 aarch64.
- **Audio**: ALSA **`AML-AUGESOUND`** card. HDMI audio on `hdmi:CARD=AMLAUGESOUND,DEV=0`
  (the SPDIF-B/TDM path — correct for this SoC despite the "dummy" naming).
- **Display**: HDMI out → **Marantz AVR** (EDID "marantz-AVR"). The AVR is the
  audio passthrough target; there is no direct TV display on the CEC bus.
- **Net**: wlan0 only (no eth0). SSH `root:coreelec` (root, NOT user coreelec),
  port 22, OpenSSH 9.9, POSIX sh.
- **Storage**: 52.6G `/storage`, 5% used (2.6G). `/storage/.kodi` 1.05G.
- **Skin**: Fen-tastic. 56 addons, all enabled.

## CEC

- The box is the **CEC master** of the living-room theater, driving the Marantz
  AVR over the kernel AOCEC bus.
- **Locked down 2026-11-05**: CEC was triggering TV/AVR shutdown (the Marantz
  doesn't respond to CEC scan — empty device list). Locked via
  `peripheral_data/cec_CEC_Adapter.xml` (enabled=0, all standby/wakeup/
  activate_source=0) + `guisettings.xml` power locks.
- CEC control exposed via `coreelec-mcp` MCP tools: `cec-scan`, `cec-power`,
  `cec-key`. No bun CEC package needed today (kernel AOCEC handles it), but
  candidates exist if a pure-bun client is wanted: `hdmi-cec`, `cec-promise`,
  `@senzil/cec-monitor`.

## Install / deps (bun)

- Controlled by the product **`coreelec-mcp`** (`@geode/coreelec-mcp`).
- Deps: `@modelcontextprotocol/sdk` + `zod` (99 pkgs installed via bun).
- Entry: `bun bin/coreelec-mcp.ts` → `play-tmdb`, `search`, `seasons`,
  `episodes`, `history`, `audit`, `recent`, `semsearch`.
- The box itself is armhf userland — aarch64/x64 bun and FFS will NOT execute
  on it. On-box search uses the pure-python `ffs-coreelec-mcp` (remote/).

## Ports (locked 2026-11-05, estate 25xxx range)

| service | old | new | config |
|---|---|---|---|
| Kodi web / JSON-RPC HTTP | 8080 | **25270** | `guisettings.xml` services.webserverport |
| slyguy proxy | 8095 | **25272** | slyguy settings.db proxy_port |
| TCP JSON-RPC | 9090 | (default) | — |

SSOT: `pens/estate/devices/coreelec/.env` (`CORELEC_RPC_PORT=25270`),
`coreelec-mcp/src/kodi.ts` default, `config/ports.env` (pending registration).

## Fleet role

- **Reference box** ("it has correct"). Dupes go 246 → 225, except tv/audio
  settings which stay per-box.
- Tools (estate-ops / kodi-fleet): `kodi-handoff`, `kodi-audit` (latency,
  addons, settings, logerrors, stalls), `kodi-resume`, `kodi-record`.
- JSON-RPC `http://10.0.0.246:25270/jsonrpc` (no auth).

## Locked state (2026-11-05 session)

1. **Audio passthrough** — PulseAudio was overriding ALSA (kodi's
   `ValidateOutputDevices` migrated to `PULSE:Default`). Disabled pulseaudio →
   kodi opens `CAESinkALSA hdmi:CARD=AMLAUGESOUND,DEV=0`, 0 sync errors.
   guisettings: samplerate=48000, ac3transcode=false, channels=8, config=3.
2. **Playback** — correct TMDB id 97 (not 31147="I-Techie") + `autoplay=true`
   via `coreelec-mcp play-tmdb 97 6 15`. Endless-loading root cause fixed.
3. **Crash** — stale 2nd kodi.bin held slyguy proxy 8095 → bind conflict →
   Python SIGSEGV. Killed stale; single kodi.bin now.
4. **Ports** — web 8080→25270, slyguy 8095→25272.
5. **CEC** — locked down (see above).

## Open issues

- Red Light spawns 6 monitor services at boot (Simkl/MDBList/PunchPlay/Expiry)
  — biggest menu-latency tax.
- Missing skin windows (nextep_handoff/sources_playback/sources_results/extras)
  — Red Light dialogs vs Fen-tastic.
- Dead scrapers stall resolution (Knaben 403, Sootio/WebStreamr/yastream
  timeouts) — `int(None)` crash patched; disable the dead ones next.
- True bitstream passthrough to Marantz not yet verified (currently PCM S16NE).

## Docs

- `devices/README.md` — device fleet overview.
- `devices/coreelec/README.md` — kodi-fleet + box inventory (now names hestia).
- `devices/coreelec/docs/box-inventory.md` — 246/225 inventory + latency.
- `devices/coreelec/docs/menu-latency.md` — menu-latency diagnosis.
- `devices/coreelec/docs/recon-and-codename.md` — this doc.
- `docs/anomalies/2026-10-30/coreelec-playback-fleet-restructure.md`.
- `docs/anomalies/2026-11-04/coreelec-internet-loss-audit.md`.
- `docs/anomalies/2026-11-05/coreelec-drew-carey-audio-fix.md`.
- `docs/anomalies/2026-11-05/coreelec-session-plan-and-complaints.md`.

## Name adoption

- `devices/coreelec/.env` — `CORELEC_NAME=hestia` added.
- `devices/coreelec/README.md` — box table names 246 · hestia, port 25270.
- `devices/coreelec/.env.example` — add `CORELEC_NAME=hestia`.
- Future fleet tooling may reference `hestia` as the canonical living-room box.