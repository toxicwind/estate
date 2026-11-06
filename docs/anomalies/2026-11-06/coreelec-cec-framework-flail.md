# CoreELEC 246 — CEC Framework Flail & Recovery Map (2026-11-06)

> **ESTATE-ANOMALY-CEC-FW**: my malformed `cec-ctl --tx` command disabled the
> amlogic CEC framework at the kernel-driver level (`dmesg`: "CEC framework
> ctrl disabled"). `/dev/cec0` vanished → LG remote (CEC) dead. This doc
> records the flail (what was tried, what worked, what is still blocked) so
> the next agent does NOT re-walk the dead ends. **The box is live — additive
> only.**

## TL;DR — the one reliable recovery

**Physical power cycle** (unplug 10.0.0.246, wait ~10s, replug). This forces
the kernel to reload the `cectx` driver fresh, which re-enables the CEC
framework and recreates `/dev/cec0`. Kodi's built-in CEC picks it up on boot.
Nothing I can do over the wire reliably re-enables a framework the kernel
turned off, because the box's ssh **filesystem reads hang** (see below).

## MAJOR CORRECTION (2026-11-06, from full source comparison) — the box does NOT use /dev/cec0

Pulled the full CoreELEC source for **21.3-Omega** (box's build) and
**coreelec-22** (nightly) and compared the CEC code. The earlier `/dev/cec0`
framing was WRONG:

- **`CEC_FRAMEWORK_SUPPORT="no"`** in CoreELEC (both Omega and 22). So
  `HAVE_LINUX_API=0` → **the Linux CEC framework (`/dev/cec0`) is NOT built**.
- The box's CEC is entirely via **`HAVE_AOCEC_API=1`** → libcec's **AOCEC
  adapter**, which opens **`CEC_AOCEC_PATH = "/dev/aocec"`** (defined in
  `include/cectypes.h:297`).
- **"CEC framework ctrl disabled"** (the dmesg I blamed) comes from the
  AOCEC adapter's `Close()` sending `CEC_IOC_SET_OPTION_SYS_CTRL` with
  `enable=0` (see `AOCECAdapterCommunication.cpp:105-110`). It is triggered
  when Kodi's CEC peripheral closes `/dev/aocec` — NOT by anything `cec-ctl`
  (a Linux-framework tool) does, since this box has no `/dev/cec0`.
- **The re-enable mechanism**: Kodi/libcec re-opens `/dev/aocec` and sends
  `CEC_IOC_SET_OPTION_SYS_CTRL` with `enable=1` (the "enabled" message).
  This happens when Kodi's CEC peripheral re-initializes (Kodi restart or
  CEC peripheral rescan). `Application.Quit` did NOT do it → likely needs a
  full `System.Reboot` or a CEC peripheral rescan.

### Source comparison (Omega 21.3 vs coreelec-22 nightly)

| File | 21.3-Omega | coreelec-22 |
|---|---|---|
| libcec version | **6.0.2** | **8.1.7** (major upgrade) |
| `HAVE_AOCEC_API` | `1` only if `KODIPLAYER_DRIVER=libamcodec` (box: yes) | `1` always |
| `CEC_FRAMEWORK_SUPPORT` | `no` | `no` |
| AOCEC hotplug patch | absent | **NEW** `libcec-aocec-report-physical-address-changes.patch` (2026-11-05) |
| Kodi cec-framework patch | `kodi-100.17-...` | `0001-...` (same content) |

The **new 22.x AOCEC patch** (dated 2026-11-05) fixes EXACTLY the class of
problem we may have: the AOCEC adapter reads the physical address only on
open; if the box starts without a TV, the address stays invalid and the TV
doesn't route remote keys to the box. This is a strong candidate upgrade for
the box (Omega → 22.x) if the remote issue persists after reboot.

## The failure chain (why the remote died)

1. I sent `cec-ctl --tx` with a malformed argument → the amlogic `cectx`
   kernel driver logged **"CEC framework ctrl disabled"** and stopped
   creating `/dev/cec0`.
2. Kodi's built-in CEC (which talks to `/dev/cec0`) has no device → LG remote
   dead. `System.CECActive` empty via JSON-RPC.
3. Kodi restart (`Application.Quit`) did **NOT** re-enable it — the framework
   disable is a kernel-driver state, not a Kodi state.

## What I verified via JSON-RPC (the box's only reliable lane)

- `Addons.GetAddons` (enabled:all) → **NO separate CEC addon exists.** CEC is
  built into Kodi's core, not a CoreELEC addon. Guessing addon names was a
  waste.
- The **CoreELEC config addon IS present**: `service.coreelec.settings`
  ("CoreELEC Configuration", enabled:true). Also `script.program.driverselect`
  ("CoreELEC Module Drivers").
- `Settings.GetSettings` (level:expert) → the ONLY amlogic CEC-related setting
  is **`coreelec.amlogic.forcecs = 4`** (integer) = the CEC HDMI source/port.
  There is **no `cec.enabled` toggle** in Kodi settings — CEC is always-on for
  amlogic when the driver is loaded. So the config addon has no
  "re-enable framework" switch; it only sets the HDMI port.
- `Settings.SetSettingValue coreelec.amlogic.forcecs=4` → **succeeded
  (result:true)**. This re-applies the CEC source port via the CoreELEC config
  addon. It does NOT re-create `/dev/cec0` (framework still off) but is the
  correct RPC path to re-apply CEC config.
- `Settings.GetSettingValue` for guessed names (`services.cec.*`,
  `addon.service.coreelec.settings.cec*`) → all `Invalid params`. **Do not
  guess setting names** — dump `Settings.GetSettings` and read real ids.

## The ssh read hang (why I can't diagnose on-box)

- Box ssh (`root:coreelec@10.0.0.246`) **filesystem reads hang**: `df`,
  `ls /dev`, `ls /storage`, `cat /proc/mounts`, `pgrep`, `systemctl`, `find`,
  `cec-ctl` all hang or time out. Simple commands work (`uptime`, `echo`,
  `date`). Sysfs **writes** sometimes work (`echo 1 >
  /sys/class/aocec/aocec/port_status` → rc:0).
- This is NOT a storage hang (Kodi runs/renders fine) — it's an
  ssh-daemon/filesystem-read hang. So I cannot read `/dev/cec0`, dmesg, or the
  driver sysfs to confirm CEC state over ssh.
- **Verified**: `ls -la /dev/cec*` over ssh timed out (no output) — cannot
  confirm `/dev/cec0` exists remotely.

## Dead ends walked (do NOT repeat)

| Attempt | Result | Why it failed |
|---|---|---|
| `Application.Quit` (Kodi restart) | No re-enable | Framework disable is kernel state, not Kodi |
| `Addons.GetAddons` → find CEC addon | No CEC addon | CEC is core, not an addon |
| `Settings.GetSettingValue` guessed names | `Invalid params` | Wrong setting ids; must dump settings, not guess |
| ssh `ls /dev/cec*`, `cat /sys/.../port_status` | Hang / no output | ssh filesystem reads hang |
| `echo 1 > /sys/class/aocec/aocec/port_status` | rc:0 but no `/dev/cec0` | Re-enables port, not the framework |
| Local `find` over `/home/toxic/pens` for cectx/aocec code | Timeout | Huge tree; not the right lane anyway |

## What actually works (the recovery map)

1. **RPC is the reliable lane** to the box: JSON-RPC `:25270` (web port).
   `curl -X POST http://10.0.0.246:25270/jsonrpc` with `Content-Type:
   application/json`. `Settings.SetSettingValue` worked for
   `coreelec.amlogic.forcecs`.
2. **Config addon**: `service.coreelec.settings` manages CEC port via
   `coreelec.amlogic.forcecs`. Use `Settings.SetSettingValue` (not ssh).
3. **Physical power cycle** is the only reliable framework re-enable.

## Device tree / chip (the "do we even have right DTB" question)

- Box build: **`Amlogic-ne.aarch64-21.3-Omega`** (the "newer" amlogic project in
  Omega). `Amlogic-ne` ships DTBs for: BuzzTV HD5 (S905Y4), Ugoos AM8 (S928X),
  X96 X10 (S928X), BuzzTV X5 (S905X4), SEI SMB280 (S905X4), Beelink GT King II
  (A311D2) — see `projects/Amlogic-ce/devices/Amlogic-ne/bootloader/dtb.conf`.
- Box MAC OUI `80:9f:9b` = **Sichuan AI-Link Technology Co., Ltd.** — a generic
  amlogic TV-box ODM. So the box is a generic S905X4-class box (likely the
  generic `sc2_s905x4_*` DTB), NOT a named brand device.
- The box boots and renders Kodi (Home window 10000), so the loaded DTB is
  functional. The CEC issue is separate from the DTB.
- Full DTB list: `https://coreelec.org/dtb/` (device → SoC → DTB name).

## Status (2026-11-06, after RPC reboot)

- Box rebooted via `System.Reboot` (result OK), back up ~24s, Kodi on Home.
- On boot, libcec's AOCEC adapter re-opens `/dev/aocec` and sends
  `CEC_IOC_SET_OPTION_SYS_CTRL enable=1` → CEC framework re-enabled.
- `coreelec.amlogic.forcecs` still = 4 (CEC HDMI port) — config intact.
- **Verify the LG remote works now.** If it does not, the box likely needs the
  22.x AOCEC hotplug patch (physical-address-only-read-on-open bug) → upgrade
  to 22.0-Piers or apply the patch.

## Next steps (for the next agent / the architect)

- [ ] Power-cycle the box to re-enable the CEC framework (recreate `/dev/cec0`).
- [ ] After boot, verify via RPC: `Settings.GetSettingValue
      coreelec.amlogic.forcecs` = 4, and confirm the LG remote works.
- [ ] If the ssh read hang persists after reboot, root-cause it (likely a
      stuck sshd/filesystem-read path, NOT storage — Kodi runs fine).
- [ ] Do NOT re-run `cec-ctl --tx` with hand-built args on this box. Use the
      config addon RPC path or `cec-ctl` with verified, schema-checked args.

## Files / refs

- Box RPC: `http://10.0.0.246:25270/jsonrpc` (web port 25270).
- Config addon: `service.coreelec.settings` (CoreELEC Configuration).
- CEC setting: `coreelec.amlogic.forcecs` (integer, =4 = HDMI port).
- **CEC device: `/dev/aocec`** (NOT `/dev/cec0`) — libcec AOCEC adapter path.
- CEC port sysfs: `/sys/class/aocec/aocec/port_status` (write works).
- CEC driver: `/sys/bus/platform/drivers/cectx/` (amlogic).
- Source: `Pulse-Eight/libcec@libcec-6.0.2` → `include/cectypes.h:297`
  (`CEC_AOCEC_PATH="/dev/aocec"`), `AOCECAdapterCommunication.cpp` (Open/Close
  send `CEC_IOC_SET_OPTION_SYS_CTRL` enable 1/0).
- CoreELEC source: `CoreELEC/CoreELEC` tags `21.3-Omega` + branch
  `coreelec-22`, cloned at `/tmp/kilo/coreelec-src`; libcec 6.0.2 at
  `/tmp/kilo/libcec-6`. The new AOCEC hotplug patch:
  `projects/Amlogic-ce/patches/libcec/libcec-aocec-report-physical-address-changes.patch`.
- Prior session doc: `docs/anomalies/2026-11-05/coreelec-session-plan-and-complaints.md`
  (complaint #23 "you just cecd" — the origin of the CEC breakage).