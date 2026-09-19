# android-fleet

ADB-managed Android devices on the LAN. Scripts live here canonically;
`/home/toxic/bin/` holds symlinks for PATH/supervisor compatibility.

## Devices (`docs/devices.md`)

| device | endpoint | access | notes |
|--------|----------|--------|-------|
| Pixel 9 Pro XL (phone) | 10.0.0.77:44933 (rotates) | wireless debugging, paired | keepalive holds the session |
| Google TV "SmartTV 4K FFM" (bedroom) | 10.0.0.225:5555 | ADB authorized 2026-09-18 | Kodi host .225 |

## Scripts (`bin/`)

- **pixel-adb-keepalive.sh** — holds the Pixel's ADB session over LAN wireless
  debugging. Reconnects every 60s; rediscovers the connect port via fast scan
  if wireless debugging rotates it. Run line in `pitchfork.toml`
  (`daemons.pixel-adb-keepalive`) points here.
