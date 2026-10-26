#!/usr/bin/env bash
# bornite (bornite) loopback launcher — binds Go binary to 127.0.0.1:HERD_PORT (25100).
# Renamed from bornite.sh — project-wide bornite naming, bornite binary kept for compatibility.
# No proxy/middleware hop. mesh-hub (25115) serves 20 GHAS /mesh/* features.
# Config: --config <main> plus --config-dir /home/toxic/estate/config/bornite.d
# (additive, watch-config hot-reload) for the kimi-auto virtual model.
# Lifecycle is owned by pitchfork (supervisor); this script does NOT kill or
# steal the port — if the bind fails, pitchfork sees the failure and retries.
set -euo pipefail
SOV="/home/toxic/estate"
# Pens overlay: the Go bornite binary lives in — and is built from —
# pens/geode/products/bornite (the canonical, newest copy); pens/ranch/... is
# a stale pre-reorg path. Search pens first, then estate, then the archived copy.
PENS="/home/toxic/pens"
source "$SOV/stack/lib-ports.sh"
require_env HERD_PORT
# Canonical secrets for provider keyEnvs (RHODOCHROSITE_API_KEY, OPENROUTER_API_KEY, ...).
# Sourced from secretsmith keyring (SSOT), never copied — keys stay in the
# keyring. ~/.secrets is legacy and no longer used.
if command -v secretsmith-env >/dev/null 2>&1; then
  set -a
  eval "$(secretsmith-env 2>/dev/null)" || true
  set +a
elif [[ -f /home/toxic/.secrets ]]; then
  set -a
  set +u
  source /home/toxic/.secrets
  set -u
  set +a
fi
PORT="$HERD_PORT"

# The dashboard is served separately from bornite now (see
# ranch/range/ui/CONSOLIDATION.md): ranch-ui on :25218 fronts the built SPA
# and proxies the bornite API same-origin. bornite's root redirect points there so
# / no longer 302s into the removed embedded /ui.
export BORNITE_DASHBOARD_URL="${BORNITE_DASHBOARD_URL:-http://127.0.0.1:25218/}"

# The binary lives beside its source in ranch/mesh/router/bornite, not under var/ (var/ is
# runtime state, and a launcher that points there means the path rots the next
# time var/ is swept). The var/bornite-backups copy is the last-known-good
# restore point if the in-tree build is ever lost. PENS paths are checked first
# because that is where the current build actually lives (pens/ranch was a
# pre-2026-10-08 reorg path; bornite's canonical source moved to pens/ranch/forge).
for BIN in \
  "$PENS/ranch/forge/router/bornite/bornite" \
  "$SOV/ranch/mesh/router/bornite/bornite" \
  "$SOV/ranch/bornite/bornite" \
  "$SOV/var/bornite-backups/bornite/bornite"
do
  [[ -x "$BIN" ]] && break
  BIN=""
done
[[ -n "$BIN" ]] || { echo "bornite bin not found in ranch/mesh/router/bornite, ranch/bornite, or var/bornite-backups/bornite" >&2; exit 1; }
CONF="$SOV/config/bornite.yaml"
[[ -f "$CONF" ]] || CONF="$SOV/config/bornite.yaml"
[[ -f "$CONF" ]] || { echo "bornite config not found at $CONF" >&2; exit 1; }

# Launch Go binary — loopback bind only (no 0.0.0.0 exposure).
# exec replaces this shell so the supervisor tracks the ACTUAL server PID,
# not a bash wrapper (2026-09-18: fixes stale-ownership where wrapper PID
# != server PID). pitchfork ready_http gates on /health; no background+wait.
exec "$BIN" --config "$CONF" --config-dir /home/toxic/estate/config/bornite.d --watch-config --listen "127.0.0.1:${PORT}"
