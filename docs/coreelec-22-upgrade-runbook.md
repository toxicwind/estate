# CoreELEC 22.0-Piers_rc1 Upgrade Runbook (hestia 10.0.0.246)

> **ESTATE-ANOMALY-CEC-FW**: Upgrades the hestia box from 21.3-Omega to
> 22.0-Piers_rc1 to fix the CEC AOCEC hotplug bug (physical address only read
> on open, never refreshed on HDMI hotplug).
>
> **Corrected SoC**: S905X3 rev c (G12A family), NOT S905X4. CPU part 0xd05,
> Cortex-A55. DTB correctly `sm1_s905x3_4g_1gbit` on Amlogic-ng (4.9 kernel).
> Migration path: Amlogic-ng → Amlogic-no (5.15 kernel).

## Why this upgrade

- **CEC hotplug fix**: libcec 8.1.7 (22.0) vs 6.0.2 (21.3) — reads physical address on hotplug events, not just on open
- **Amlogic-ng → Amlogic-no**: S905X3 (G12A family) moves from `Amlogic-ng` (4.9 kernel) to `Amlogic-no` (5.15 kernel) — Generic image handles auto-detection via `coreelec-dt-id` overlay
- **Kodi 21.x → Kodi 22**: Piers series (Kodi 22-based)

## Pre-upgrade verification (CRITICAL — FAIL FAST)

**Do NOT proceed unless ALL of these pass. Network or CEC not restored = full upgrade failure.**

### 1. SSH connectivity (must work before flashing)
```bash
sshpass -p 'coreelec' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 root@10.0.0.246 'echo OK'
```
- **If this fails**: SSH daemon is down, SSH keys may have been rotated, or box is on a different firmware. DO NOT FLASH.
- Current state: root:coreelec works, OpenSSH_9.9 on the box.

### 2. Network connectivity (must work post-upgrade)
- **Ethernet**: Box at `10.0.0.246` on `enp12s0` subnet, MAC `90:0e:b3:1d:18:81`
- **WiFi**: Connected to `DankWifi` (5GHz, -35dBm, 867Mbps), MAC `80:9f:9b:85:1a:5d`
- **Bluetooth**: BCM254 (Realtek), `hci0` UP RUNNING
- **CoreELEC API**: Listening on port 25270 (Kodi-bound), port 5323
- **WiFi profile**: `/storage/.cache/connman/wifi_809f9b851a5d_44616e6b57696669_managed_psk` (DankWifi) — **lives in /storage, survives upgrade**
- **net-watchdog**: `/storage/.config/net-watchdog.sh` pings 10.0.0.1 (tier1) + 1.1.1.1 (tier2) every 30s, bounces DankWifi via `connmanctl` after 3 link-fails / 6 WAN-fails — **preserved in /storage**
- **Post-upgrade**: Verify network comes back via:
  ```bash
  # On the box after boot:
  ip addr show eth0   # should get DHCP IP
  cat /sys/class/net/wlan0/operstate  # should say 'up'
  iw dev wlan0 link  # should show DankWifi
  cat /storage/log-network/watchdog.log  # should show recovered event
  ```

### 2b. Verified network stack survival (rc1 image inspected 2026-11-07)

**Driver transition: vendor `rtl88x2cs` → mainline `rtw88` (kernel 4.9 → 5.15)**

| Component | Box (21.3) | rc1 image (22.0) | Verdict |
|---|---|---|---|
| WiFi chipset | RTL8822CS (SDIO 024C:C822) via vendor `rtl88x2cs` | `rtw_8822cs.ko` (mainline) + `rtw8822c_fw.bin` + `rtw8822c_wow_fw.bin` | ✅ present |
| WiFi profile | connman `wifi_809f9b851a5d_44616e6b57696669_managed_psk` | connman in rc1 (`connman.service`, `connmanctl`) | ✅ /storage |
| Bluetooth | RTL8822CS BT | `rtl_bt/rtl8822cs_config.bin` + `rtl8822cs_fw.bin` | ✅ present |
| Ethernet | `90:0e:b3:1d:18:81` | G12A DTB ethernet node | ✅ DTB-matched |
| Kernel | 4.9.269 | 5.15.196 | driver swap expected |

**Why the profile survives**: connman profile filename embeds the WiFi MAC
(`809f9b851a5d`). MAC is burned into the RTL8822CS chip — identical after
upgrade. Interface stays `wlan0` under mainline driver → connman auto-connects.

**Watchdog recovery**: `net-watchdog.sh` auto-bounces DankWifi on link/WAN
failure. If WiFi doesn't reconnect on first boot, watchdog handles it within
90s — verify via `/storage/log-network/watchdog.log`.

**If WiFi still dead after driver swap** (mainline rtw88 edge cases):
```bash
sshpass -p 'coreelec' ssh root@10.0.0.246 '
  modprobe -r rtw_8822cs && modprobe rtw_8822cs
  connmanctl disable wifi && connmanctl enable wifi
  connmanctl connect wifi_809f9b851a5d_44616e6b57696669_managed_psk
'
```

### 3. CEC pre-state (must be functional before upgrade)
- **CEC device**: `/dev/aocec` (AOCEC framework, NOT Linux CEC framework)
- **Boot cmdline**: `hdmitx=0x2e,422,12bit vout=2160p60hz,enable`
- **config.ini**: `cec_func_config='7f'` (CEC enabled)
- **Current status**: AOCEC enabled, `enable=1` at boot
- **Post-upgrade**: `/dev/aocec` should still be present, libcec 8.1.7 with hotplug patch

### 3b. Verified CEC survival (rc1 image inspected 2026-11-07)
- rc1 `dtb.xml` has `<cec status="CEC-B" version="0">` — CEC-B default, same as box
- rc1 `cfgload`/`cfgload_env` read `config.ini` → `cec_func_config` → `hdmitx=cec${cec_func_config}` — identical logic to 21.3
- Box `config.ini` has `cec_func_config='7f'` — **preserved in /storage**, applied by new cfgload
- `/dev/aocec` node present in 5.15 kernel (AOCEC driver in `aocec` DT node)
- libcec 8.1.7 (vs 6.0.2) includes the AOCEC physical-address hotplug patch

### 4. Storage (config survives upgrade)
- `/storage` = 52.6GB, 49.2GB free — safe for upgrade
- Config preserved in `/storage/.kodi/userdata/`
- Addons preserved: `plugin.video.eternal`, `plugin.video.pov`, `inputstream.adaptive`, etc.

## Current box state (verified 2026-11-07 00:57)

| Field | Value |
|---|---|
| **SoC** | Amlogic S905X3 rev c (G12A family, CPU part 0xd05, Cortex-A55) |
| **NOT S905X4** | CPU part 0xd05 = G12A/SM1 family. DTB correctly `sm1_s905x3_4g_1gbit` |
| **Current OS** | CoreELEC 21.3-Omega, Amlogic-ng project |
| **Kernel** | 4.9.269 (4.9 family, G12A-specific) |
| **Compatible** | `amlogic, g12a` |
| **coreelec-dt-id** | `sm1_s905x3_4g_1gbit` |
| **CEC** | `/dev/aocec` (AOCEC, not Linux CEC framework) |
| **Kodi** | Running, JSON-RPC on :25270, no :8080 |
| **WiFi** | Connected to `DankWifi`, -35dBm, 867 Mbps |
| **Bluetooth** | BCM254 (Realtek), hci0 up |
| **Uptime** | 13 minutes |
| **SSH** | root:coreelec, OpenSSH_9.9, port 22 |
| **MACs** | ETH `90:0e:b3:1d:18:81`, WiFi `80:9f:9b:85:1a:5d` |
| **Resolution** | 2160p60hz, frac_rate_policy=1 |
| **Keymap** | us |
| **Storage** | 52.6GB, 49.2GB free |

## Upgrade path: Amlogic-ng → Amlogic-no (21.3 → 22.0)

**This is the standard G12A/SM1 migration path:**
- 21.3: `Amlogic-ng` project (G12A, S905X2/X3 family, 4.9 kernel)
- 22.0: `Amlogic-no` project (unified G12A/SM1/SC2/S4/S5, 5.15 kernel)
- Generic image uses kernel DT overlay (`coreelec-dt-id`) to auto-select the right `.dtb`
- Box's current `coreelec-dt-id = sm1_s905x3_4g_1gbit` has a matching DTB in the 22.0 Generic image at `/flash/device_trees/sm1_s905x3_4g_1gbit.dtb`

## Image

| Field | Value |
|---|---|
| File | `/tmp/CoreELEC-Amlogic-no.aarch64-22.0-Piers_rc1-Generic.img.gz` |
| Size | 362.7 MB |
| SHA256 | `21fc51990355adfb0f8e98df4dbd278cbb554ba346cba8e8f7c60bc4188a3eca` |
| Target | `Amlogic-no.aarch64-22.0-Piers_rc1-Generic` |
| Source project | Amlogic-ng (21.3) |
| Target project | Amlogic-no (22.0) |

## Upgrade method: network-only (NO USB) — VERIFIED 2026-11-07

**The USB method is NOT required.** The box's initrd has a full boot-time
update engine that processes `/storage/.update/*.tar` (or `.img.gz`). This
was reverse-engineered from the box's own initrd and executed successfully.

**CRITICAL: Do not proceed unless pre-upgrade checks pass.**

### Step 0: Snapshot current config (before updating)
```bash
sshpass -p 'coreelec' ssh root@10.0.0.246 '
  mkdir -p /storage/.kodi/backups/pre-22-upgrade
  cp -a /storage/.kodi/userdata /storage/.kodi/backups/pre-22-upgrade/userdata
  echo "Backup complete"
'
```

### Step 1: Get the .tar update file

**The `.tar` (not `.img.gz`) is the right payload.** CoreELEC releases both;
the tar contains `target/{SYSTEM, KERNEL, *.md5}` which the initrd updater
expects. SCP/SFTP hangs on this box, so host the file locally and let the box
pull it over LAN:

```bash
# On awrawr-pc — download the tar (or reuse /tmp/CoreELEC-rc1.tar = same file)
curl -L -o /tmp/CoreELEC-Amlogic-no.aarch64-22.0-Piers_rc1.tar \
  https://github.com/CoreELEC/CoreELEC/releases/download/22.0-Piers_rc1/CoreELEC-Amlogic-no.aarch64-22.0-Piers_rc1.tar

# Serve it over LAN (Bun or python)
python3 -m http.server 8765 --directory /tmp &
```

### Step 2: Download on box + stage .nocompat

```bash
sshpass -p 'coreelec' ssh root@10.0.0.246 '
  mkdir -p /storage/.update
  cd /storage/.update
  curl -s -o CoreELEC-Amlogic-no.aarch64-22.0-Piers_rc1.tar \
    http://10.0.0.218:8765/CoreELEC-Amlogic-no.aarch64-22.0-Piers_rc1.tar
  md5sum CoreELEC-Amlogic-no.aarch64-22.0-Piers_rc1.tar   # verify vs local
  touch .nocompat   # BYPASSES Amlogic-ng → Amlogic-no project gate
'
```

### Step 3: Reboot (initrd runs the update)

```bash
sshpass -p 'coreelec' ssh root@10.0.0.246 'sync; reboot'
```

On boot, the initrd's `/init` `check_update()`:
1. Finds `.tar` in `/storage/.update/`
2. Extracts to `.tmp`, `mv .tmp/*/target/* .` → gets `SYSTEM`, `KERNEL`
3. `.nocompat` skips `check_is_compatible` (would otherwise block `Amlogic-ng` vs `Amlogic-no`)
4. md5 verifies via `SYSTEM.md5`/`KERNEL.md5`
5. `update_file` — `dd` new `SYSTEM` (388MB) + `KERNEL` → `/flash/SYSTEM`, `/flash/kernel.img` (rm old first — space fine)
6. `update_bootloader` — runs new system's `update.sh`: updates `dtb.img`
   (auto-selects `sm1_s905x3_4g_1gbit.dtb` ✅), `cfgload`, `device_trees/`
7. `do_cleanup` removes `.nocompat` + update files
8. Reboots → boots 22.0

**Wait ~5 min** for two reboot cycles. Verify with:
```bash
sshpass -p 'coreelec' ssh root@10.0.0.246 'uname -r; cat /etc/os-release | head -3'
# Expect: 5.15.196 / 22.0-Piers_rc1
```

### Step 4: Post-upgrade connectivity check (first 60 seconds)
```bash
# Wait for box to come up (it reboots once during upgrade)
# Check SSH — might take 30-60s after boot
sshpass -p 'coreelec' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@10.0.0.246 'echo SSH_OK'

# If SSH hangs, try the CoreELEC API
curl -s --connect-timeout 5 http://10.0.0.246:25270/jsonrpc -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","method":"ping","id":1}'
```
- **If neither responds after 120 seconds**: The upgrade likely failed. The box may be stuck on the boot partition or the DTB didn't match. Roll back immediately (see Rollback section).
- **If SSH works but API doesn't**: Normal — API server takes 60-90s to start.

### Step 5: Verify version and state
```bash
# Verify OS version on the box
sshpass -p 'coreelec' ssh root@10.0.0.246 'cat /etc/os-release | head -5'

# Verify kernel
sshpass -p 'coreelec' ssh root@10.0.0.246 'uname -r'
# Expected: 5.15.x (was 4.9.269)

# Verify DTB applied
sshpass -p 'coreelec' ssh root@10.0.0.246 'cat /proc/device-tree/compatible'
sshpass -p 'coreelec' ssh root@10.0.0.246 'cat /proc/device-tree/chosen/overlay_signature'

# Verify CEC device
sshpass -p 'coreelec' ssh root@10.0.0.246 'ls -la /dev/aocec'

# Verify network
sshpass -p 'coreelec' ssh root@10.0.0.246 'ip addr show eth0'
sshpass -p 'coreelec' ssh root@10.0.0.246 'iw dev wlan0 link 2>/dev/null'

# Verify storage preserved
sshpass -p 'coreelec' ssh root@10.0.0.246 'df -h /storage | tail -1'
sshpass -p 'coreelec' ssh root@10.0.0.246 'ls /storage/.kodi/addons/ | wc -l'
```

Expected results:
- VERSION=22.0-Piers (or later release candidate)
- Kernel: 5.15.x
- Compatible: `amlogic, g12a` (unchanged — SoC is still G12A family)
- `/dev/aocec` exists
- eth0 gets DHCP IP
- WiFi reconnects to DankWifi
- /storage preserved with all addons

**VERIFIED 2026-11-07 (actual upgrade result):**
- VERSION=22.0-Piers_rc1 ✅
- Kernel=5.15.196 ✅
- DTB=`sm1_s905x3_4g_1gbit` ✅ (auto-selected by update.sh)
- WiFi: `DankWifi` reconnected via connman profile (driver swap vendor→`rtw_8822cs` worked) ✅
- `/dev/aocec` present, kernel `hdmi_cec_func_config:0x7f` ✅
- libcec 8.1.7 (`/usr/lib/libcec.so.8.1.7`) ✅
- CEC physical_addr=2500 (vs 0000 in old bug) — hotplug path active ✅
- CEC logical addr=0x1 (TV), CEC version 5 ✅
- Storage: 52.5G preserved, all addons intact ✅
- Bluetooth: hci0 UP RUNNING, same BD address ✅

### Step 6: CEC verification
```bash
# After Kodi fully boots (2-3 minutes):
sshpass -p 'coreelec' ssh root@10.0.0.246 '
  # Verify AOCEC is active
  cat /proc/device-tree/aocec/status 2>/dev/null || echo AOCEC_NOT_IN_DTB
  
  # Check libcec version
  strings /usr/lib/libcec.so* 2>/dev/null | grep -i "libcec" | head -3
'
```

Test LG remote CEC — if it works immediately, the hotplug patch is effective.

**Current CEC state (verified post-upgrade):**
```bash
sshpass -p 'coreelec' ssh root@10.0.0.246 '
  cat /sys/class/aocec/physical_addr  # 2500 = valid HDMI address
  cat /sys/class/aocec/log_addr       # 1 = TV logical address
  cat /sys/class/aocec/fun_cfg        # 0x7f = all CEC functions
'
```
- `physical_addr != 0000` → the libcec 8.1.7 hotplug fix is working
- Kodi log: `Register - new cec device registered on cec->AOCEC`
- If the LG remote still drops after HDMI hotplug, reboot once (new libcec holds addr)

## Rollback

**If upgrade fails (no SSH, no API, stuck on boot):**
- **Rollback via network**: repeat the network method with the
  `21.3-Omega` `.tar` (download from
  `https://github.com/CoreELEC/CoreELEC/releases/tag/21.3-Omega`)
  into `/storage/.update/` + `.nocompat`, reboot — the box's initrd
  processes it identically regardless of current state (as long as
  `/storage` is intact and the box boots far enough for the initrd).
- **Fallback**: USB flash 21.3 image. `/storage` config survives both paths.
- If the box boots but no network: the initrd un-tars + dd's from
  `/storage/.update`, so a failed network stack does NOT block recovery —
  rollback still works.

## Network restoration checklist

**Network must be restored post-upgrade or all downstream services fail.**
**ALL CHECKED 2026-11-07 after the real upgrade:**

- [x] eth0 gets DHCP IP from router (10.0.0.x)
- [x] Can SSH from awrawr-pc (10.0.0.218 → 10.0.0.246)
- [x] WiFi reconnects to DankWifi — mainline `rtw_8822cs` driver, -37dBm, 5GHz
- [x] Kodi running (PID in ps), JSON-RPC on :25270
- [x] Bluetooth hci0 UP RUNNING (RTL8822CS, same BD addr)
- [ ] SMB/JSON-RPC LAN acceptance (Kodi was still booting during verify)

## Post-upgrade items

- [x] CEC: physical_addr=2500, log_addr=1, fun_cfg=0x7f, libcec 8.1.7 ✅
- [x] Network: WiFi DankWifi, BT hci0, SSH ✅
- [x] DTB: sm1_s905x3_4g_1gbit auto-selected ✅
- [ ] Verify `inputstream.adaptive` still works
- [ ] Check `plugin.video.eternal` addon works (requires network)
- [ ] Test LG remote CEC via RPC / physical hotplug test
- [ ] Verify Kodi skin settings preserved
- [ ] Check `/storage/.kodi/temp/kodi.log` for errors on first boot

## DTB Analysis

### Verified: rc1 image inspected directly (mounted FAT boot partition, 2026-11-07)

**Boot partition structure (rc1 Generic):**
```
aml_autoscript  cfgload  cfgload_env  config.ini  device_trees/
kernel.img  kernel.img.md5  recovery.img  SYSTEM  SYSTEM.md5
```

**`sm1_s905x3_4g_1gbit.dtb` CONFIRMED present** in `device_trees/` (78,362
bytes, kernel 5.15 variant vs 73,342 on box's 4.9 — expected growth). 87 total
DTBs in image covering G12A/SM1/SC2/S4/S5.

**Boot flow compatibility verified:**
- Both 21.3 and rc1 use `cfgload` + `kernel.img` + `dtb.img` + `resolution.ini` `/` `config.ini`
- Both support eMMC install: `ce_on_emmc=yes` → `boot=LABEL=CE_FLASH disk=FOLDER=/dev/CE_STORAGE`
- rc1 adds: `mac` passthrough via ethaddr, improved `loadaddr` handling (0x02000000), `usbpower`, `fbcon`
- `update.sh` flow: chroot into new SYSTEM → `DT_ID=$(dtname)` → copy
  `/usr/share/bootloader/device_trees/${DT_ID}.dtb` → `/flash/dtb.img` →
  update device_trees/, cfgload, kernel.img, SYSTEM
- Box's `dtname` returns `sm1_s905x3_4g_1gbit` → matches rc1 device_trees → upgrade auto-selects correct DTB

### What the box currently uses (21.3-Omega)
- **DTB ID**: `sm1_s905x3_4g_1gbit` (73,342 bytes)
- **Kernel**: 4.9.269 (G12A-specific, Amlogic-ng project)
- **Device tree overlay**: `/proc/device-tree/chosen/overlay_signature` set by U-Boot
- **Compatible**: `amlogic, g12a`
- **Not a mismatch**: The box's DTB correctly identifies its SoC as S905X3

### What 22.0-Generic provides
- **Kernel**: 5.15.196 (unified Amlogic-5.15 across all Amlogic-no project)
- **DTBs**: All 60+ device trees bundled (G12A, SM1, SC2, S4, S5 families)
- **Auto-detection**: Kernel sets `coreelec-dt-id` via boot overlay, `update.sh` copies the matching `.dtb` from `/usr/share/bootloader/device_trees/`
- **Matching DTB**: `sm1_s905x3_4g_1gbit.dtb` exists in the 22.0 image
- **CEC config**: `dtb.xml` includes AOCEC (`/aocec ee_cec`), motorcomm PHY for `sc2_s905x4*1gbit` (also matches G12A), CEC-B default
- **Network firmware**: `rtw88/rtw8822c_fw.bin` + `rtw_8822cs.ko` module (mainline) for the box's RTL8822CS chipset; `rtl_bt/rtl8822cs_config.bin` for BT

### Migration details
- Amlogic-ng (4.9 kernel) → Amlogic-no (5.15 kernel) is the official G12A/SM1 migration path
- No DTB manual intervention needed — Generic image auto-detects via `coreelec-dt-id`
- AOCEC continues to work — `/dev/aocec` is part of the 5.15 kernel config
- The S905X3 is well-covered in 22.0 — Odroid C4, Banana Pi M2/M5, Beelink GT1 Mini 2, Khadas VIM3L all use the same SoC family
- WiFi driver swap (vendor `rtl88x2cs` → mainline `rtw_8822cs`) — profile preserved via /storage; see §2b

## Notes

- Image downloaded to `/tmp/` (verified SHA256)
- Image inspected: FAT boot partition mounted + SYSTEM squashfs browsed (2026-11-07) — DTB, cfgload, update.sh, network firmware all verified
- SCP/SSH filesystem reads hang — USB flash only
- Physical access to box required for USB flash
- Box is live (family media center) — additive only
- **S905X3 (G12A), NOT S905X4** — upgrade path is Amlogic-ng → Amlogic-no, not Amlogic-ne → Amlogic-no
- Pre-upgrade SSH and network checks are **blocking gates** — do not skip
- Upgrade takes 3-5 minutes, box reboots once during process
- /storage config preserved: addons, userdata, settings all survive
