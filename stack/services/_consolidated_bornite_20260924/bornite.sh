#!/usr/bin/env bash
# bornite (bornite) loopback launcher — binds Go binary to 127.0.0.1:HERD_PORT (25100).
# Renamed from bornite.sh — project-wide bornite naming, bornite binary kept for compatibility.
# No proxy/middleware hop. mesh-hub (25115) serves 20 GHAS /mesh/* features.
# Config: --config <main> plus --config-dir /home/toxic/kimi-auto/bornite.d
# (additive, watch-config hot-reload) for the kimi-auto virtual model.
# Lifecycle is owned by pitchfork (supervisor); this script does NOT kill or
# steal the port — if the bind fails, pitchfork sees the failure and retries.
set -euo pipefail
SOV="/home/toxic/estate"
source "$SOV/stack/lib-ports.sh"
require_env HERD_PORT
# Canonical secrets for provider keyEnvs (RHODOCHROSITE_API_KEY, OPENROUTER_API_KEY, ...).
# Sourced from secretsmith keyring (SSOT). ~/.secrets is legacy.
if command -v secretsmith-env >/dev/null 2>&1; then
  set -a
  eval "$(secretsmith-env 2>/dev/null)" || true
  set +a
fi  # ~/.secrets deleted 2026-10-26 — keyring is the only source
PORT="$HERD_PORT"
BIN="$SOV/projects/bornite/bornite"
[[ -x "$BIN" ]] || { echo "bornite (bornite) bin not found at $BIN" >&2; exit 1; }
CONF="$SOV/config/bornite.yaml"
[[ -f "$CONF" ]] || CONF="$SOV/config/bornite.yaml"
[[ -f "$CONF" ]] || { echo "bornite config not found at $CONF" >&2; exit 1; }

# Launch Go binary — loopback bind only (no 0.0.0.0 exposure).
# exec replaces this shell so the supervisor tracks the ACTUAL server PID,
# not a bash wrapper (2026-09-18: fixes stale-ownership where wrapper PID
# != server PID). pitchfork ready_http gates on /health; no background+wait.
exec "$BIN" --config "$CONF" --config-dir /home/toxic/kimi-auto/bornite.d --watch-config --listen "127.0.0.1:${PORT}"
