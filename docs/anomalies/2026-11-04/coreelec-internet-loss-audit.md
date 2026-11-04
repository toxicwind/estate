# CoreELEC 246 (10.0.0.246) internet-loss audit — 2026-11-04 (corrected)

## Symptom
Box "loses internet over and over." Perception = recurring ~14s full
dropouts of wlan0. **User correlation: it happens when the TV loses its
Marantz AVR connection over eARC and the box closes (suspends).**

## Root cause (CORRECTED 2026-11-04)
**HDMI-CEC standby.** The CoreELEC box's CEC adapter config
(`/storage/.kodi/userdata/peripheral_data/cec_CEC_Adapter.xml`) had
`standby_pc_on_tv_standby = 13011` (enabled). When the TV drops the
Marantz over eARC, the TV sends a CEC standby; the box follows it into
standby/suspend → wlan0 drops → "loses internet" and the box "closes."
The wifi "disconnects" (06:16, 10:17) were CEC power-off/suspend events,
NOT AP kicks.

## Evidence
- `/dev/aocec` (char 502:0) + `[cec_work]` kernel thread — Amlogic CEC
  driver live; Kodi drives it via `/usr/lib/libcec.so` (libCEC).
- `cec_CEC_Adapter.xml`: `standby_pc_on_tv_standby=13011` (box follows TV
  standby), `enabled=1`, `standby_tv_on_pc_standby=1`.
- journalctl: 8 `operstate 2 <DOWN>` events today = suspend/resume cycles.
- Driver power mgmt clean (`power_mgnt=0`, `ips_mode=0`, `enusbss=0`).

## Fix (applied 2026-11-04, live-verified)
1. **`standby_pc_on_tv_standby` set to `0`** in
   `cec_CEC_Adapter.xml` — the box no longer goes to standby when the TV
   does. This is the real root-cause fix.
2. New headless CEC control tools in coreelec-mcp (`cec-scan`, `cec-power`,
   `cec-key`, `cec-settings`) to drive the TV + Marantz over `/dev/aocec`
   via libCEC without touching the live UI — committed + pushed
   (coreelec-mcp 011c538).
3. Credential moved to keyring SSOT (`COREELEC_SSH_PASSWORD`).

## Retracted (superseded by CEC finding)
- The net-watchdog systemd unit (ping-gateway bounce) was a band-aid for
  the wrong diagnosis. **Disabled** (`systemctl disable net-watchdog`).
- The connman `Frequency=2437` pin experiment caused an outage (box
  needed a power cycle) and is not the fix — reverted by power-cycle
  (box re-associated to 5 GHz 5785 on boot).

## Contract test
`grep standby_pc_on_tv_standby cec_CEC_Adapter.xml` = value 0; TV
dropping the Marantz over eARC no longer suspends the box (wlan0 stays
up). `cec-scan` over coreelec-mcp enumerates TV + Marantz on the bus.

## Follow-ups
- Confirm the CEC fix survives a Kodi restart (setting is read at
  peripheral init; a Kodi reload applies it cleanly).
- If TV/AVR control is wanted, use the new coreelec-mcp CEC tools
  headlessly (no UI).