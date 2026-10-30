# Box inventory (2026-10-30)

## 246 — CoreELEC (living room, reference box)

- Host 10.0.0.246 (wlan0 only — no eth0), CoreELEC 21.3-Omega / Amlogic-ng.arm,
  Kodi compiled 2025-11-04 (`/storage/.kodi`).
- SSH: `root` / `coreelec` (user `coreelec` does NOT work; root does), port 22,
  OpenSSH 9.9, shell is POSIX sh (not bash).
- JSON-RPC http://10.0.0.246:8080/jsonrpc, no auth (webserver on).
- Hardware: Amlogic S905X3 (`sm1_s905x3_4g_1gbit` dt-id), 4× Cortex-A55
  (part 0xd05), 3.8G RAM, kernel 4.9.269 aarch64.
- Disk: 52.6G `/storage`, 5% used (2.6G). `/storage/.kodi` 1.05G total.
- Skin: Fen-tastic (skin.fentastic + script.fentastic.helper).
- Audio: ALSA `AML-AUGESOUND`, passthrough on.
- 56 addons, all enabled.
- Full env: `.env` (gitignored) / `.env.example` (template).

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
