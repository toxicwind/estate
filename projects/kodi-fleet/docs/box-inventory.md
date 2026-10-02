# Box inventory (2026-09-18)

## 246 — CoreELEC (living room, reference box)

- Host 10.0.0.246, Kodi 21.x on CoreELEC (`/storage/.kodi`).
- SSH: `root` / `coreelec` (user `coreelec` does NOT work; root does).
- JSON-RPC http://10.0.0.246:8080/jsonrpc, no auth.
- Disk: 52.6G `/storage`, 4% used. `.kodi/addons` 160M, `.kodi/userdata` 248M.
- Skin: Fen-tastic (+ script.fentastic.helper).
- Audio: ALSA `AML-AUGESOUND`, passthrough on.
- 71 addons, all enabled.

## 225 — Android / Google TV (bedroom)

- Host 10.0.0.225, Kodi 21.2 Android.
- No SSH. JSON-RPC http://10.0.0.225:8080/jsonrpc, no auth.
- Skin: Nimbus (+ script.nimbus.helper).
- Audio: `AUDIOTRACK:AudioTrack` (plain PCM path; the `(RAW)` IEC device
  breaks audio when passthrough is off — fixed 2026-09-18).
- 106 addons, all enabled (35 not on 246).

## Network latency (JSON-RPC Ping x10, from awrawr-pc)

- 246: min 6.8ms, p50 8.5ms, max 13.3ms, avg 8.4ms
- 225: min 9.2ms, p50 13.3ms, max 78.4ms, avg 26.6ms (one 78ms spike)

Network path is healthy on both; UI sluggishness is not the LAN.
See `menu-latency.md`.
