#!/usr/bin/env bash
# Tailscale Funnel control — single backend (no Caddy).
# Funnel is optional public edge. Prefer Tailscale MagicDNS to :25100 directly.
set -euo pipefail

FUNNEL_PORT="${RANCH_UI_PORT:-25218}"
SOV_LOG="/home/toxic/estate/.state/logs"

case "${1:-}" in
  up)
    mkdir -p "$SOV_LOG"
    if [ -f /home/toxic/estate/config/ports.env ]; then
      set -a
      # shellcheck disable=SC1091
      source /home/toxic/estate/config/ports.env
      set +a
      FUNNEL_PORT="${RANCH_UI_PORT:-25218}"
    fi
    tailscale funnel --bg "${FUNNEL_PORT}"
    echo "[tailscale] funnel up on :${FUNNEL_PORT} (ranch dashboard; not a multipath reverse proxy)"
    exec tail -f /dev/null
    ;;
  down)
    tailscale funnel reset
    echo "[tailscale] funnel reset (disabled)"
    ;;
  status)
    tailscale funnel status
    ;;
  *)
    echo "usage: funnel.sh {up|down|status}"
    exit 1
    ;;
esac
