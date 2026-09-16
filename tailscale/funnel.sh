#!/usr/bin/env bash
# Tailscale Funnel control — single backend (no Caddy).
# Funnel is optional public edge. Prefer Tailscale MagicDNS to :25100/:25101 directly.
set -euo pipefail

FUNNEL_PORT="${RUST_WEB_PORT:-25101}"
SOV_LOG="/home/toxic/sovereign/.state/logs"

case "${1:-}" in
  up)
    mkdir -p "$SOV_LOG"
    if [ -f /home/toxic/sovereign/config/ports.env ]; then
      set -a
      # shellcheck disable=SC1091
      source /home/toxic/sovereign/config/ports.env
      set +a
      FUNNEL_PORT="${RUST_WEB_PORT:-25101}"
    fi
    tailscale funnel --bg "${FUNNEL_PORT}"
    echo "[tailscale] funnel up on :${FUNNEL_PORT} (rust-web ops; not a multipath reverse proxy)"
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
