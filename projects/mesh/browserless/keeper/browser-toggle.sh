#!/bin/bash
# browser-toggle.sh: show/hide the keeper Chromium window via Hyprland scratchpad.
# Wired to the Quickshell bar button (quickshell/BrowserToggle snippet).
#
# This Hyprland build dispatches through Lua (hl.*); classic
# "movetoworkspace special:browser,address:0x..." syntax is rejected.
# Correct forms (from pyprland lua_translate.py + hl.dsp.window.move):
#   hide: hl.dsp.window.move({workspace="special:browser", follow=false, window="address:0x..."})
#   show: hl.dsp.window.move({workspace="e+0", window="address:0x..."}) + hl.dsp.focus({window="address:0x..."})
#
# The keeper window is identified by the PID of the chrome main process
# holding --remote-debugging-port=9223 on the nv-audit profile, so the
# users personal Chromium is never touched.
set -u

if [ -z "${HYPRLAND_INSTANCE_SIGNATURE:-}" ]; then
  for d in /run/user/1000/hypr/*/; do
    sig="$(basename "$d")"
    if HYPRLAND_INSTANCE_SIGNATURE="$sig" hyprctl clients -j >/dev/null 2>&1; then
      export HYPRLAND_INSTANCE_SIGNATURE="$sig"
      break
    fi
  done
fi

KEEFER_PID=""
for p in $(pgrep -f "remote-debugging-port=9223" 2>/dev/null); do
  cmd="$(tr "\0" " " < "/proc/$p/cmdline" 2>/dev/null)"
  case "$cmd" in
    *"user-data-dir=/home/toxic/.browserless/profiles/nv-audit"*)
      case "$cmd" in
        *"--type="*) ;;
        *) KEEFER_PID="$p"; break ;;
      esac
      ;;
  esac
done

if [ -z "$KEEFER_PID" ]; then
  notify-send "Browser keeper" "keeper Chromium is not running" 2>/dev/null || true
  exit 1
fi

INFO="$(hyprctl clients -j | python3 -c "import json,sys
cs=json.load(sys.stdin)
for c in cs:
    if str(c.get(\"pid\")) == \"$KEEFER_PID\":
        print(str(c.get(\"address\",\"\")) + \"|\" + str(c.get(\"workspace\",{}).get(\"name\",\"\")))
        break
")"

if [ -z "$INFO" ]; then
  notify-send "Browser keeper" "keeper window not found" 2>/dev/null || true
  exit 1
fi

ADDR="${INFO%%|*}"
WS="${INFO##*|}"
SEL="address:$ADDR"

if [[ "$WS" == *"special"* ]]; then
  hyprctl dispatch "hl.dsp.window.move({workspace=\"e+0\", window=\"$SEL\"})" > /dev/null
  hyprctl dispatch "hl.dsp.focus({window=\"$SEL\"})" > /dev/null
else
  hyprctl dispatch "hl.dsp.window.move({workspace=\"special:browser\", follow=false, window=\"$SEL\"})" > /dev/null
fi
