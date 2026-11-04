#!/usr/bin/env bash
# clip-mirror — mirror the HOST Wayland clipboard into the keeper Xvnc :99.
#
# WHY (2026-11-03, architect: "allow copy paste in keeper"): TigerVNC
# vncviewer is an X11 app running under XWayland (:0). Wayland-native apps
# (wezterm, chromium) own the wl clipboard; XWayland exports it lazily — X11
# clients that only observe selection-CHANGE events (vncviewer's FLTK event
# loop) never see wl-native ownership transfers, so ClientCutText never
# reaches Xvnc :99 and paste into the keeper is empty.
#
# FIX: poll the wl clipboard (wl-paste) and push any change straight into
# the :99 CLIPBOARD selection with xclip. vncviewer needs no change; paste
# inside keeper just works. The :99→host direction is unaffected (keeper
# copies arrive as ServerCutText → vncviewer sets the local clipboard).
#
# Contract:
#  - mirrors text clipboard only (images out of scope)
#  - 0.5s poll; wl-paste fails (empty/no owner) → keep last value
#  - skips no-op sets (avoid re-owning with identical content)

set -u
KEEPER_DISPLAY="${KEEPER_DISPLAY:-:99}"
POLL_SECONDS="${CLIP_MIRROR_POLL:-0.5}"

last=""
while true; do
	text="$(wl-paste --no-newline 2>/dev/null)" || { sleep "$POLL_SECONDS"; continue; }
	if [ -n "$text" ] && [ "$text" != "$last" ]; then
		last="$text"
		printf '%s' "$text" | xclip -display "$KEEPER_DISPLAY" -selection clipboard -i 2>/dev/null
		echo "$(date +%H:%M:%S) mirrored ${#text} chars → $KEEPER_DISPLAY"
	fi
	sleep "$POLL_SECONDS"
done
