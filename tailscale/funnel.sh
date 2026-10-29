#!/usr/bin/env bash
# Tailscale Funnel control — public entrypoints on the dedicated doorbell-node
# funnel instance (github-mcp-host.tailc9ac71.ts.net).
#
# Each public entrypoint gets an ORTHOGONAL, independent fence (it is never
# correct to funnel straight at an unauthenticated backend):
#   /           -> 127.0.0.1:25217  doorbell oauth-edge (deny-by-default bearer
#                                   gate; proxies authed traffic to :25202, the
#                                   loopback-only, no-auth upstream). Public
#                                   host-shell access is only reachable through a
#                                   valid bearer token.
#   /squawk-ws  -> 127.0.0.1:25147  squawk-ws (own feed token, independent of the
#                                   doorbell gate).
#
# This is a durable, idempotent declaration: re-running `up` re-applies the full
# route set, so a dropped control socket / node restart self-heals. It is wired
# as the pitchfork daemon `tailscale-funnel` (estate/pitchfork.toml).
#
# Tailscale serve-config requires root (`sudo tailscale ...`). On this box sudo
# is passwordless, so the script prefixes sudo when the plain command is denied,
# preferring the non-root operator path first.
set -euo pipefail

SOCK="${TAILSCALE_FUNNEL_SOCK:-/run/tailscale/doorbell.sock}"
DOORBELL_EDGE="${DOORBELL_OAUTH_EDGE_PORT:-25217}"
SQUAWK_WS="${SQUAWK_WS_PORT:-25147}"

wsock() {
  # Tailscale serve-config needs root unless `sudo tailscale set --operator=$USER`
  # was run once. Try the non-root path first (works on operator-enabled hosts);
  # on "serve config denied" fall back to passwordless sudo.
  if tailscale --socket="$SOCK" "$@" 2>/tmp/tfunnel.err; then
    return 0
  fi
  if grep -q "serve config denied\|Access denied" /tmp/tfunnel.err 2>/dev/null; then
    sudo tailscale --socket="$SOCK" "$@"
  else
    cat /tmp/tfunnel.err >&2
    exit 1
  fi
}

# Declare both public routes. Idempotent: passing --set-path again replaces the
# existing backend for that path; if the route is gone it is recreated.
funnel_up() {
  mkdir -p /home/toxic/pens/estate/.state/logs  # legacy: keep for funnel.sh; SSOT is pens/estate
  if [ -f /home/toxic/pens/estate/config/ports.env ]; then
    set -a
    # shellcheck disable=SC1091
    source /home/toxic/pens/estate/config/ports.env
    set +a
    DOORBELL_EDGE="${DOORBELL_OAUTH_EDGE_PORT:-25217}"
    SQUAWK_WS="${SQUAWK_WS_PORT:-25147}"
  fi
  wsock funnel --bg --set-path=/ "http://127.0.0.1:${DOORBELL_EDGE}"
  wsock funnel --bg --set-path=/squawk-ws "http://127.0.0.1:${SQUAWK_WS}"
  echo "[tailscale] funnel up: / -> oauth-edge :${DOORBELL_EDGE} (bearer fence); /squawk-ws -> :${SQUAWK_WS}"
}

case "${1:-}" in
  up)
    funnel_up
    exec tail -f /dev/null
    ;;
  down)
    wsock funnel reset
    echo "[tailscale] funnel reset (disabled)"
    ;;
  status)
    wsock funnel status
    ;;
  *)
    echo "usage: funnel.sh {up|down|status}"
    exit 1
    ;;
esac