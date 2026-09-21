#!/usr/bin/env bash
# browser-router.sh — the one router for every Chromium on this box.
#
# Chris: "you keep targeting wrong place make sure you have a router"
#
# ROUTES
#   user      Chris's desktop Chromium — Hyprland/wayland, his real profile:
#             all Muse UI windows + YouTube. Opening anything here RAISES the
#             window (focus steal — reads as a mouse takeover). Use ONLY on
#             his direct order. Never for background automation.
#   agent     Isolated agent Chromium — Xvnc :99 (RFB 127.0.0.1:5900, noVNC
#             :6080 INTERACTIVE on loopback (external: token-gated
#             funnel /agent-browser -> gate :6081), CDP 127.0.0.1:9223,
#             profile nv-audit.
#             DEFAULT for all agent browsing. Zero Hyprland/input impact.
#   ephemeral browserless 2.x at 127.0.0.1:25130 — throwaway sessions, no
#             logins. Scrape-and-forget work.
#
# Usage:
#   browser-router.sh status              # which routes are alive
#   browser-router.sh open user <url>     # new tab in Chris's browser
#   browser-router.sh open agent <url>    # new tab in isolated browser (CDP)
#   browser-router.sh tabs user           # list his session URLs (read-only)
set -euo pipefail

CHROMIUM_BIN=/usr/lib/chromium/chromium
CDP_AGENT=http://127.0.0.1:9223

die() { echo "router: $*" >&2; exit 1; }

route_alive() {
  case "$1" in
    user)      pgrep -f 'chromium.*--ozone-platform=wayland' >/dev/null 2>&1 ;;
    agent)     curl -sf --max-time 3 "$CDP_AGENT/json/version" >/dev/null 2>&1 ;;
    ephemeral) code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 http://127.0.0.1:25130/config 2>/dev/null); [ "$code" = "401" ] || [ "$code" = "200" ] ;;
    *) die "unknown route: $1 (user|agent|ephemeral)" ;;
  esac
}

cmd_status() {
  for r in user agent ephemeral; do
    if route_alive "$r"; then echo "$r: alive"; else echo "$r: DOWN"; fi
  done
}

cmd_open() {
  local route="$1" url="$2"
  case "$route" in
    user)
      # Attach to the running desktop instance; never pass --user-data-dir.
      WAYLAND_DISPLAY=wayland-1 XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/1000}" \
        "$CHROMIUM_BIN" --new-tab "$url" >/dev/null 2>&1 &
      echo "opened in user browser: <url>"
      ;;
    agent)
      route_alive agent || die "agent browser not running (CDP $CDP_AGENT unreachable)"
      local enc
      enc=$(python3 -c 'import urllib.parse,sys; print(urllib.parse.urlencode({"url":sys.argv[1]}))' "$url")
      curl -sf --max-time 10 -X PUT "$CDP_AGENT/json/new?$enc" >/dev/null \
        || die "CDP open failed"
      echo "opened in agent browser: $url"
      ;;
    ephemeral)
      die "ephemeral open not wired yet — use browserless /playwright API directly"
      ;;
    *) die "unknown route: $route" ;;
  esac
}

cmd_tabs() {
  # read-only: pull URLs from the desktop Chromium's session files
  [ "$1" = user ] || die "tabs only supports the user route"
  strings /home/toxic/.config/chromium/Default/Sessions/Session_* 2>/dev/null \
    | grep -oE 'https://[^ "\\]+' | sort -u | head -50
}

case "${1:-}" in
  status) cmd_status ;;
  open)   [ $# -eq 3 ] || die "usage: $0 open <user|agent> <url>"; cmd_open "$2" "$3" ;;
  tabs)   [ $# -eq 2 ] || die "usage: $0 tabs user"; cmd_tabs "$2" ;;
  *)      die "usage: $0 {status|open <route> <url>|tabs user}" ;;
esac
