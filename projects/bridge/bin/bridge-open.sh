#!/usr/bin/env bash
# bridge-open — the router for opening URLs in the desktop Chromium.
#
# The bridge's physical display (Hyprland on DP) runs one Chromium singleton.
# This router hands URLs to THAT instance, verifies each handoff landed, and
# if a launcher lingers (handoff failed) kills exactly the PIDs born from
# that launch so a rogue main can never be left behind.
#
# NEVER run bare `chromium --new-tab` (or headless/headed automation without
# --user-data-dir) against the default profile: automation runs poison the
# desktop singleton registration with stale Singleton* files, and later
# --new-tab launches become rogue mains instead of handing off. (2026-09-21)
set -euo pipefail

PROFILE=/home/toxic/.config/chromium
LOG=/tmp/bridge-open.log

[ $# -ge 1 ] || { echo "usage: bridge-open <url> [url...]" >&2; exit 2; }

as_toxic() {
  local wd
  wd=$(basename "$(ls -d /run/user/1000/wayland-* 2>/dev/null | head -1)")
  sudo -u toxic env WAYLAND_DISPLAY="$wd" XDG_RUNTIME_DIR=/run/user/1000 \
    XDG_CURRENT_DESKTOP=Hyprland \
    "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus" "$@"
}

# Browser main PIDs (excludes --type= children: zygote, gpu, renderer...).
browser_mains() {
  pgrep -f '/usr/lib/chromium/chromium' 2>/dev/null | while read -r p; do
    if tr '\0' '\n' < "/proc/$p/cmdline" 2>/dev/null | grep -q -- '--type='; then
      continue
    fi
    echo "$p"
  done
}

kill_rogues() {
  local before="$1" p b born c
  for p in $(browser_mains | sort -u); do
    born=1
    for b in $before; do [ "$p" = "$b" ] && born=0; done
    [ "$born" -eq 0 ] && continue
    c=$(tr '\0' ' ' < "/proc/$p/cmdline" 2>/dev/null | cut -c1-100)
    echo "bridge-open: killing rogue main $p :: $c" >&2
    kill -9 "$p" 2>/dev/null || true
  done
}

# One URL per launch: Chromium only reliably opens the first URL when
# several are passed in a single invocation (2026-09-21).
rc=0
for url in "$@"; do
  before=$(browser_mains | sort -u)
  as_toxic /usr/bin/chromium --new-tab "$url" </dev/null >>"$LOG" 2>&1 &
  LAUNCHER=$!

  # Handoff check: a successful handoff exits the launcher within ~10s.
  ok=0
  for _ in $(seq 1 40); do
    kill -0 "$LAUNCHER" 2>/dev/null || { ok=1; break; }
    sleep 0.25
  done

  if [ "$ok" -eq 1 ]; then
    echo "bridge-open: handed to desktop chromium :: $url"
  else
    echo "bridge-open: handoff FAILED for $url — removing rogue launcher tree" >&2
    kill_rogues "$before"
    kill -9 "$LAUNCHER" 2>/dev/null || true
    rc=1
  fi
done
exit "$rc"
