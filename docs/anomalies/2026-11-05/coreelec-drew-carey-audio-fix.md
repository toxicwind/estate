# 2026-11-05 CoreELEC 246 — Drew Carey playback + HDMI audio fix (session log)

## Goal
Play "The Drew Carey Show" S06E15 on CoreELEC S905X3 (10.0.0.246) with working
HDMI audio passthrough to the Marantz AVR, and fix the endless-loading / crash /
sync-error failures.

## Root causes found (in order of discovery)

### 1. Wrong TMDB id → endless loading (metadata + scraper crash)
- I used `tmdb_id=31147` which resolves to **"I-Techie"** (0 seasons), NOT Drew
  Carey. The real Drew Carey Show TMDB id is **97** (same as trakt id, coincidentally).
- With the wrong id, `metadata.tvshow_meta()` returned a show with 0 seasons,
  so `data['season']` became the string `'None'` → every external scraper
  (SNOWFLAKE/KONTRAST/KNABEN/LIMETORRENTS) crashed with
  `invalid literal for int() with base 10: 'None'` → endless "loading" + lag.
- Verified: `curl "https://api.themoviedb.org/3/search/tv?query=The Drew Carey Show&api_key=7b2b17..."` → id 97.

### 2. Missing `autoplay=true` → source picker blocked playback headless
- `playback.media` is a *resolver* route. Without `autoplay=true` it opens the
  sources_results.xml picker (window 13007/13002) and waits for a user pick.
  Headless that dialog can't focus ("Control 2000 ... can't focus") → nothing plays.
- Fix: inject `autoplay=true` into the plugin URL. The existing
  `coreelec-mcp` product does this via `withAutoplay()`.

### 3. PulseAudio overriding ALSA → AVR sync errors
- CoreELEC (LibreELEC derivative) runs pulseaudio system-wide. Kodi's
  `ValidateOutputDevices` migrated the saved `ALSA:hdmi...` device to
  `PULSE:Default`, even with `--audio-backend=alsa` and `KODI_AE_SINK=ALSA`.
- PulseAudio resamples to PCM and cannot bitstream-passthrough. Result:
  massive `ActiveAE - large audio sync error: -6000..-25000ms` and
  `CDVDAudio::AddPacketsRenderer - timeout`. AVR couldn't lock.
- Fix: `systemctl stop pulseaudio && systemctl disable pulseaudio`. Kodi now
  opens `CAESinkALSA hdmi:CARD=AMLAUGESOUND,DEV=0`, 0 sync errors.

### 4. Dual kodi.bin process → port conflict → SIGSEGV crash
- Two kodi.bin processes were running. A stale one (PID 5225) held port
  **8095** (slyguy proxy) + 1060. Fresh kodi's slyguy proxy failed to bind →
  `[Errno 98] Address already in use` → Python `PyList_New()` SIGSEGV → crash.
- Fix: `kill -9 5225`. Now exactly 1 kodi.bin. Ports 8095/1060 freed.

## Fixes applied
- **Audio backend**: stopped + disabled pulseaudio (persistent).
- **guisettings.xml** (`/storage/.kodi/userdata/guisettings.xml`):
  - `audiooutput.samplerate` = 48000
  - `audiooutput.ac3transcode` = false
  - `audiooutput.channels` = 8
  - `audiooutput.config` = 3
  - `audiooutput.audiodevice` / `passthroughdevice` = `ALSA:hdmi:CARD=AMLAUGESOUND,DEV=0`
- **Play**: `bun bin/coreelec-mcp.ts play-tmdb 97 6 15 --host=10.0.0.246`
  (injects `autoplay=true`).

## Final verified state
- Playing: Drew Carey Show S06E15 "Drew's in a Coma (2)", ~10-14%, speed 1.
- 0 sync errors.
- 1 kodi.bin process.
- Audio sink: `CAESinkALSA`, device `hdmi:CARD=AMLAUGESOUND,DEV=0,AES0=0x04,AES1=0x82,AES2=0x00,AES3=0x02`, format S16NE (PCM, not yet bitstream).

## Remaining / open
- Prevent stale-kodi respawn on boot (kodi.sh wrapper has a restart loop; a
  second instance can re-grab ports). Consider a single-instance guard.
- External scrapers still crash with `int('None')` on every scrape (lag source)
  — root is missing/None season in scrape data; likely only fixed by correct
  metadata, but the scraper should guard `int(None)`.
- Knaben API 403 Forbidden (aiostreams instance).
- True bitstream passthrough to Marantz not yet verified (currently PCM S16NE).
  Need an AC3/DTS source to confirm the AVR receives bitstream.

## Key files
- `/storage/.config/kodi.conf` → `KODI_AE_SINK=ALSA`
- `/storage/.kodi/userdata/guisettings.xml`
- `/storage/.kodi/userdata/addon_data/plugin.video.redlight/settings.xml` (autoplay)
- `/home/toxic/pens/geode/products/coreelec-mcp/` (play-tmdb tool)
- Crash logs: `/storage/.kodi/temp/kodi_crashlog_20261104210049.log`