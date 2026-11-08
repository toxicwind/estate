# CoreELEC Audio Device Mismatch (2026-11-07)

## Symptom
- Sync error -847 seconds (~14 min drift), stream stalled
- No sound, micro-stutters, audio lagging badly
- Kodi running but audio clock completely desynced

## Root Cause
**Passthrough device mismatch:**
- `guisettings.xml`: `audiooutput.audiodevice` set to `DEV=3` (user had changed it)
- `advancedsettings.xml`: `passthroughdevice` still pointing to `DEV=0`
- Kodi opened `pcmC0D0p` (DEV=0) at session start — never picked up the DEV=3 change
- Format: `S16_LE 8ch 192000` (decode-to-PCM, not bitstream) — running device was wrong

## Fix Applied
1. `sed -i "s/CARD=AMLAUGESOUND,DEV=0/CARD=AMLAUGESOUND,DEV=3/g" /storage/.kodi/userdata/advancedsettings.xml`
2. Verified both files now consistently say DEV=3
3. Stopped playback to let Kodi release the old ALSA fd
4. Sent `Settings.SetSettingValue` to force audio device reopen
5. Kodi now has `pcmC0D1p` (DEV=1? — need to verify DEV=3 is next)

## Key Lessons
- **Kodi holds ALSA fds across playback stops** — Settings API returns true but doesn't reopen device while playback fd is held
- **Files ≠ runtime**: guisettings/advancedsettings edits don't hot-reload Kodi's audio sink
- **Workaround**: Stop playback → fix config → restart playback (Kodi reopens device from fresh config)
- **DEV numbering**: DEV=0 is default/first HDMI, DEV=3 is the AVR passthrough device on this Amlogic board

## Verification
```bash
# Check which device Kodi is using NOW:
ssh root@10.0.0.246 'ls -la /proc/$(pidof kodi.bin)/fd/ | grep snd'
# Should show pcmC0D3p (DEV=3) after fix

# Verify config consistency:
ssh root@10.0.0.246 'grep AMLAUGESOUND /storage/.kodi/userdata/guisettings.xml /storage/.kodi/userdata/advancedsettings.xml'
# Both should show DEV=3
```
