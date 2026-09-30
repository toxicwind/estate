# android-fleet

ADB-managed Android devices on the LAN — Chris's Pixel 9 Pro XL and the bedroom Google TV. Scripts live here canonically; `/home/toxic/bin/` holds symlinks for PATH/supervisor compatibility.

<div align="right">

[![license: MIT](https://img.shields.io/badge/license-MIT%20%2B%20upstream-blue?style=for-the-badge)](https://github.com/toxicwind/sovereign-projects#license)
[![sovereign-projects](https://img.shields.io/badge/sovereign--projects-main-6e56cf?style=for-the-badge)](https://github.com/toxicwind/sovereign-projects)

</div>

## Why this exists

The fleet's reach ends where ADB begins — unless someone holds the sessions open. Wireless debugging ports rotate, TVs need on-screen approval, and a dropped session at 2am means no deploys until morning. This project keeps both devices reachable: a keepalive daemon that rediscovers the Pixel's rotating port, and documented, approved access to the TV that unlocks direct Kodi file deploys.

## Devices (`docs/devices.md`)

| Device | Endpoint | Access | Notes |
|---|---|---|---|
| Pixel 9 Pro XL (Chris's phone) | 10.0.0.77:44933 (rotates) | wireless debugging, paired | keepalive holds the session; port rediscovered via fast scan on rotation |
| Google TV "SmartTV 4K FFM" (bedroom) | 10.0.0.225:5555 | ADB authorized 2026-09-18 | Kodi host .225 — direct file deploys, no more JSON-RPC-only limit |

```mermaid
flowchart TB
    subgraph lan[LAN 10.0.0.0/24]
        PIXEL[Pixel 9 Pro XL<br/>10.0.0.77:44933<br/>wireless debugging]
        TV[Google TV "SmartTV 4K FFM"<br/>10.0.0.225:5555<br/>Kodi 21.2]
    end
    subgraph yote[awrawr-pc]
        KA[pixel-adb-keepalive.sh<br/>pitchfork daemon<br/>reconnect 60s · port rescan 30000-50000]
        ADB[/usr/bin/adb]
    end
    KA -->|holds session| PIXEL
    ADB -->|shell · push · pull| TV
    TV -.->|unlocks| KODI[kodi-fleet deploys<br/>forked addons · settings · log reads]
```

## Scripts (`bin/`)

- **pixel-adb-keepalive.sh** — holds the Pixel's ADB session over LAN wireless debugging. Reconnects every 60s; rediscovers the connect port via fast port scan (30000–50000) when wireless debugging rotates it. One-time pairing done 2026-09-17 (pairing persists in `/home/toxic/.android/adbkey*`, survives phone reboot). Run line in `pitchfork.toml` (`daemons.pixel-adb-keepalive`) points here. Additive only: never touches other adb devices (emulator-5554 etc.). Replaced the old Tailscale tcpip target (100.123.57.58:5555, dropped 2026-09-17 per Chris: "new one drop other").

## Quick start

```bash
adb -s 10.0.0.77:44933 shell            # Pixel (port rotates — keepalive tracks it)
adb -s 10.0.0.225:5555 shell            # Google TV
adb -s 10.0.0.225:5555 push addon.zip /sdcard/   # Kodi file deploy
```

## Config

- Pixel pairing: `adb pair 10.0.0.77:<pair-port>` (one-time, code from the phone's "Pair with pairing code" screen). Keys in `/home/toxic/.android/adbkey*`.
- TV authorization: approved on the TV dialog 2026-09-18 (was `unauthorized` until Chris approved it).
- Kodi data on the TV: `/sdcard/Android/data/org.xbmc.kodi/files/.kodi/`.

## License & security

MIT where marked — [LICENSE](https://github.com/toxicwind/sovereign-projects#license). ADB is root-equivalent on the device — these are Chris's personal devices on his LAN. The pairing keys (`/home/toxic/.android/adbkey*`) are credentials: never commit, never share. Keepalive is additive-only by design (never touches other adb devices).
