#!/bin/bash
# browser-toggle.sh: show/hide the keeper Chromium window via Hyprland scratchpad.
# Wired to the Quickshell bar button (quickshell/BrowserToggle snippet).
set -u
if [ -z "${HYPRLAND_INSTANCE_SIGNATURE:-}" ]; then
  HYPRLAND_INSTANCE_SIGNATURE="$(ls /run/user/1000/hypr/ 2>/dev/null | head -n 1)"
  export HYPRLAND_INSTANCE_SIGNATURE
fi
SCRATCH="browser"
ADDR="$(hyprctl clients -j | python3 -c "import json,sys; cs=json.load(sys.stdin); print(next((c.get(\"address\",\"\") for c in cs if \"chrom\" in ((c.get(\"class\") or \"\")+\" \"+(c.get(\"initialClass\") or \"\")).lower()), \"\"))")"
if [ -z "$ADDR" ]; then
  notify-send "Browser keeper" "keeper Chromium window not found" 2>/dev/null || true
  exit 1
fi
ON_SPECIAL="$(hyprctl clients -j | python3 -c "import json,sys; cs=json.load(sys.stdin); print(any(c.get(\"address\")==\"$ADDR\" and \"special\" in str(c.get(\"workspace\",{}).get(\"name\",\"\")) for c in cs))")"
if [ "$ON_SPECIAL" = "True" ]; then
  hyprctl dispatch movetoworkspace "e+0,address:$ADDR" > /dev/null
  hyprctl dispatch focuswindow "address:$ADDR" > /dev/null
else
  hyprctl dispatch movetoworkspace "special:$SCRATCH,address:$ADDR" > /dev/null
fi
