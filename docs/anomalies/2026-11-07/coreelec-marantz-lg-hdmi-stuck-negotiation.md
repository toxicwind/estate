# CoreELEC box → Marantz AVR → LG TV: stuck HDMI negotiation + CEC address/hijack (hestia 10.0.0.246, 2026-11-07)

> **ESTATE-ANOMALY-HDMI-CEC-FREEZE**: After the CoreELEC 22.0-Piers_rc1 upgrade reboot, the
> box's picture would not appear on the LG TV (LG "no signal"/gallery wallpaper on HDMI2)
> even though the box, Marantz SR6013, and LG were all individually healthy. Root cause was a
> **stuck HDMI TMDS negotiation** between the box and the AVR monitor chain — **not** a dead
> device, **not** a color-depth/8-bit problem (it eventually locked at the box's native
> 1080p60@12-bit).

## Topology

```
CoreELEC box (hestia, 10.0.0.246, Amlogic S905X3, CE22.0-Piers_rc1)
   └─ HDMI OUT ──> Marantz SR6013 (AVR, HDMI input, phys 2.5.0.0)
                      └─ HDMI MONITOR/eARC OUT ──> LG TV HDMI2 (eARC)  [10.0.0.176, rooted SSH]
```

- Box's EDID (`/sys/class/amhdmitx/amhdmitx0/edid`): `Rx Product Name: marantz-AVR`,
  `Source Physical Address: 2.5.0.0`, `MaxTMDSClock1 225 MHz`, `SCDC: 0` (HDMI 1.4-era AVR).
- LG `port2` EDID physical address `2.0.0.0` = HDMI2 (the eARC port).

## Symptom
- Box output looked "correct" (Kodi running, DRM connected, encoder clock present) but the TV
  showed no-signal wallpaper on HDMI2.
- The box's CEC advertised the wrong physical address and (after it was corrected) began
  **hijacking** the AVR, so the user could not switch the AVR to HEOS or other inputs.
- CEC menu / adapter reported `(0000:0000)` / ioctl errors.

## Diagnostics — read BOTH kernels (untruncated)

### Box side (10.0.0.246, root@, sshpass)
```bash
cat /sys/class/amhdmitx/amhdmitx0/clkmsr          # cts_hdmi_tx_pixel_clk present (~148M for 1080p60) => box IS driving
cat /sys/class/amhdmitx/amhdmitx0/attr            # e.g. 444,12bit  (this reflects negotiated output)
cat /sys/class/amhdmitx/amhdmitx0/disp_mode        # VIC:16 = 1080p60
cat /sys/class/amhdmitx/amhdmitx0/cedst_count     # "clock undetected / CH0-2 unlocked"
cat /sys/class/drm/card0-HDMI-A-1/status           # connected
cat /sys/class/drm/card0-HDMI-A-1/modes            # full list incl. 1080p60hz
# Kodi recurring line (NOISE, not the real fault):
#   CAMLDRMUtils::aml_init_drmDevice - connector of drmDevice is not connected
#   CWinSystemAmlogic - HotplugEvent mode switch ignored while HDMI DRM connector is not ready (1 modes)
```
- `cedst` "clock undetected / CH unlocked" is a **red herring** on an HDMI 1.4 sink with
  `SCDC: 0` (no clock-return echo) — once the TV locks, cedst still reads that way. Trust the TV lock, not cedst.

### TV side (10.0.0.176, prisoner@:9922, rooted)
```bash
grep -hE "PHY Lock\[[0-9]\]|ClkDetect|Ch[0-9]~2Locked|timing_active_[wh]|phy_lock_status|Stable CNT|VIC Code|Sig:|TMDS Clk|Pixel Clk" \
  /proc/lg/hdmi20/port2/status /proc/lgtv-driver/hdmi_status/hdmi.p2
```
- Before fix: `PHY Lock[0]`, `scdc_clk_detect:0`, `scdc_ch0/1/2_locked:0`, `timing_active_w:0`,
  and the RAW sync read a **fractional clock** (e.g. ~40 MHz @ ~16 Hz for a 148 MHz box signal —
  roughly 1/2–1/4) at EVERY box mode including 480p. Data islands (SPD `Amlogic MBox Meson Ref`)
  still reaching the TV = the AVR was re-embedding packets but not passing a lockable clock.
- After fix: `PHY Lock[1]`, `timing_active_w:1920`, `timing_active_h:1080`,
  `timing_v_freq:600` (60 Hz), `TMDS 222.53 MHz`.

## Root cause
A **stuck HDMI TMDS negotiation** between the box TX and the AVR's monitor re-timer. It
manifested as the AVR re-emitting a fractional/non-lockable clock (audio/eARC stayed up because
that's a separate lane). It was **not** a dead box, not a dead AVR, not a 12-bit ceiling (the TV
later locked the box's native 1080p60@12-bit). The "AVR half/divides the clock while eARC audio
works" signature is the fingerprint for this class.

## Fix (what finally worked)

### 1. Break the stuck negotiation — force the box through mode re-sets
Repeatedly forced `disp_mode` re-sets / Kodi restarts **until the TV reported a real lock**
(`PHY Lock[1]` + `timing_active_w`/`timing_v_freq` > 0). Once broken out, the box locked at its
**native default** `1080p60 @ 444,12bit` (VIC 16, 148 MHz) — so no depth/colorspace change was
ultimately required. Watch the TV side each iteration; stop the instant `timing_active_w:1920`.

### 2. Correct the CEC physical address (behind an AVR)
In `/storage/.kodi/userdata/peripheral_data/cec_CEC_Adapter.xml`:
`<setting id="physical_address" value="0x1000"/>` (libCEC's HDMI-1 default) was WRONG — the box is
at **`2.5.0.0`** (TV HDMI2 → AVR input 5). Fix:
```bash
sed -i 's/0x1000/0x2500/' /storage/.kodi/userdata/peripheral_data/cec_CEC_Adapter.xml
systemctl restart kodi
```
Verify the box now broadcasts `<Active Source 2.5.0.0>` (`dmesg | grep "msg: 1f 82"` → `25 00`,
not `10 00`).

### 3. Stop the CEC hijack (box force-selecting the AVR, blocking HEOS/other inputs)
After the address fix the box (configured `activate_source=1`) began force-claiming the source,
so you couldn't switch the AVR. To make the box passive:
```bash
sed -i -e 's|activate_source" value="1"|activate_source" value="0"|' \
       -e 's|wakeup_cec_active_route" value="1"|wakeup_cec_active_route" value="0"|' \
       -e 's|wakeup_cec_streaming" value="1"|wakeup_cec_streaming" value="0"|' \
       -e 's|wakeup_cec_auto_power" value="1"|wakeup_cec_auto_power" value="0"|' \
       /storage/.kodi/userdata/peripheral_data/cec_CEC_Adapter.xml
systemctl restart kodi
```
Keep `physical_address` at the correct `0x2500` so the box is still discoverable/controllable but
does not hijack the AVR. (`activate_source=0` means the box won't auto-select on boot — flip to
`1` if auto-input-switch is preferred.)

## Contract test
```bash
# TV must report a real, lockable signal:
ssh -i ~/.ssh/lg-tv_webos_trad -p 9922 -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedAlgorithms=+ssh-rsa prisoner@10.0.0.176 \
 'grep -hoE "PHY Lock\[[0-9]\]|timing_active_w:[0-9]+|timing_v_freq:[0-9]+" /proc/lgtv-driver/hdmi_status/hdmi.p2 /proc/lg/hdmi20/port2/status'
# expect: PHY Lock[1]  timing_active_w:1920  timing_v_freq:600
```

## Gotchas (learned the hard way)
- **`cedst` "clock undetected" is NOT proof the link is down on an SCDC-off HDMI-1.4 sink** — the
  TV lock is truth.
- **Kodi's `connector not ready (1 modes)` log is recurring noise** when the box is still driving
  (148 MHz clock present); do not chase it as the root cause.
- **The box's sysfs `attr` is effectively read-only** (`rc=1` on write, even mode-disabled); the
  driver pins color depth from the sink's EDID — don't burn time trying to force 8-bit via sysfs
  (`coreelec.amlogic.limitcd/forcecs` in Kodi are the real, limited levers).
- **`avmute` toggles / CEC power-on to a power-cycled AVR won't break a stuck TMDS negotiation** —
  the forced `disp_mode` re-set is what does.
- Verify any change through the TV kernel (the "tv side"), not just the box — both sides read
  cleanly and cross-checked.