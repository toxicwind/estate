#!/bin/bash
# browser-toggle.sh: show/hide the keeper Chromium window via Hyprland scratchpad.
# Wired to the Quickshell bar button (quickshell/BrowserToggle snippet).
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
