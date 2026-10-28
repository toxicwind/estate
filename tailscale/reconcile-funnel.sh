#!/usr/bin/env bash
# Self-healing Tailscale funnel reconciler for the public github-mcp-host routes.
#
# The public funnel routes:
#   /          -> 127.0.0.1:25217  doorbell oauth-edge (deny-by-default bearer gate)
#   /squawk-ws -> 127.0.0.1:25147  squawk-ws (own feed token)
#
# tailscale funnel routes on the doorbell-node instance are stored by that
# node's tailscaled, but the node can drop/restart its funnel control socket,
# which makes the public URL vanish ("public URL dropped for a few seconds").
# This daemon re-applies the route set on a short interval so a dropped route
# self-heals. It runs under pitchfork (`estate/tailscale-funnel` daemon) with a
# health check against the public ping route.
set -uo pipefail

SOCK="${TAILSCALE_FUNNEL_SOCK:-/run/tailscale/doorbell.sock}"
INTERVAL="${FUNNEL_RECONCILE_INTERVAL:-30}"
DOORBELL_EDGE="${DOORBELL_OAUTH_EDGE_PORT:-25217}"
SQUAWK_WS="${SQUAWK_WS_PORT:-25147}"

if [ -f /home/toxic/estate/config/ports.env ]; then
  set -a
  # shellcheck disable=SC1091
  source /home/toxic/estate/config/ports.env
  set +a
  DOORBELL_EDGE="${DOORBELL_OAUTH_EDGE_PORT:-25217}"
  SQUAWK_WS="${SQUAWK_WS_PORT:-25147}"
fi

reconcile() {
  # Apply/reconcile both routes. `--set-path` replaces the backend for an
  # existing path and (re)creates a dropped one. Try the non-root path first;
  # fall back to passwordless sudo on "serve config denied".
  if tailscale --socket="$SOCK" funnel --bg --set-path=/ "http://127.0.0.1:${DOORBELL_EDGE}" \
      && tailscale --socket="$SOCK" funnel --bg --set-path=/squawk-ws "http://127.0.0.1:${SQUAWK_WS}"; then
    return 0
  fi
  sudo tailscale --socket="$SOCK" funnel --bg --set-path=/ "http://127.0.0.1:${DOORBELL_EDGE}" >/dev/null 2>&1
  sudo tailscale --socket="$SOCK" funnel --bg --set-path=/squawk-ws "http://127.0.0.1:${SQUAWK_WS}" >/dev/null 2>&1
  return 0
}

while true; do
  reconcile
  sleep "$INTERVAL"
done