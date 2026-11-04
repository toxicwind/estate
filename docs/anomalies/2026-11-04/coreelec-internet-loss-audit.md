# CoreELEC 246 (10.0.0.246) internet-loss audit — 2026-11-04

## Symptom
Box "loses internet over and over." Perception = recurring ~14s full
dropouts of wlan0.

## Evidence (live probes, ssh root@10.0.0.246, pw in keyring
COREELEC_SSH_PASSWORD)
- wlan0 (rtl88x2cs, kernel 4.9.269) on SSID DankWifi, **5 GHz ch157
  (5785 MHz)**, signal −41 dBm, tx 867 Mbit/s, power_save already OFF.
- journalctl (RAM-backed, volatile): 8 `operstate 2 <DOWN>` events, all
  today — 06:16:07 single `CTRL-EVENT-DISCONNECTED reason=0`
  (unspecified = AP-side kick), 10:17:18–22 flap cluster (4 DOWNs within
  seconds during reassociation), recovered 10:17:30 via connman
  auto-reconnect (~14s gateway→online).
- dmesg shows only 2 ADDRCONF link-up events in 4d13h uptime — kernel
  sees far fewer events than connman/wpa layer.
- No autoscripts, no cron, no userland toggler on the box — drops are
  AP-side (mesh AP, locally-administered BSSID 52:bb:9f:62:8b:12) or
  Realtek driver-side, NOT caused by the box.
- Same SSID also broadcast on 2.4 GHz ch6 at −30 dBm (stronger), but
  connman merges same-SSID BSSIDs into one service — no band pinning.
- Kodi log: 0 connection-lost lines (dropouts too short to trip Kodi).

## Root cause
AP-side disconnects (reason=0) + flappy reassociation; client recovers
but unbounded and unlogged (volatile journal = no history to audit).

## Hardening (installed 2026-11-04, live-verified)
1. `/storage/.config/net-watchdog.sh` + systemd unit
   `/storage/.config/system.d/net-watchdog.service` (enabled, active):
   ping gateway 10.0.0.1 every 30s; 3 consecutive fails → bounce the
   connman wifi service; one JSON line per state change to
   `/storage/log-network/watchdog.log` (persistent).
2. Credential moved to keyring SSOT (`COREELEC_SSH_PASSWORD`, attrs
   host/user) — was tribal-knowledge only.

## Contract test
`systemctl is-active net-watchdog` = active; watchdog.log exists and
stays empty while pings pass; next AP kick produces a
`{"event":"bounce"}` line within ~90s and recovery ≤ 60s after.

## Follow-ups (not done here)
- AP side: check mesh node logs for the 06:16/10:17 kicks; if the AP
  supports it, prefer a non-mesh-steered channel or disable band
  steering for this client's MAC 80:9F:9B:85:1A:5D.
- rtl88x2cs driver params not exposed via modinfo on this build;
  firmware/driver bump would need a CoreELEC update (out of scope).
