#!/usr/bin/env bash
# funnel-map.sh — durable tailscale Funnel serve-map declaration for yote.
#
# WHY THIS EXISTS (2026-09-21, penstock):
#   tailscale serve/funnel mounts are NOT kept in a config file. The CLI
#   writes them into tailscaled's state DB at /var/lib/tailscale/tailscaled.state
#   (key _serve/<id>, value is a base64+zlib-encoded serve-config blob).
#   That state file survives tailscaled restarts, so CLI-applied mounts are
#   restart-safe — the failure mode is state wipe / host re-provisioning,
#   after which the whole map must be re-applied. THIS script is that
#   re-application path, and the only committed record of the full map.
#
#   Probe gotcha (verified): funnel binds 443 on the TAILNET IPs only
#   (e.g. 100.72.199.93), never 127.0.0.1. Probing via
#   --resolve <dns>:443:127.0.0.1 gives an all-000 false wedge. Verify via
#   the tailnet IP with correct SNI — lane-probe.sh does this right.
#
# USAGE: sudo ./funnel-map.sh [--check]
#   --check : report only; exit 1 if any declared mount is missing.
#   (default): idempotently add missing mounts. Existing mounts are skipped:
#   `tailscale funnel --bg --set-path` errors "listener already exists" on
#   duplicates, so skip-if-present is load-bearing, not polite.
#
# ADDING A NEW MOUNT: append one line to MAP below, run the script as root,
# then verify with lane-probe.sh (it parses all serve paths and probes each
# through the public funnel URL).
#
# /openfang placement (2026-09-21 full audit): /openfang -> mesh-front proxy on
# 127.0.0.1:25103 (OpenFang Dashboard UI), fronting the :25196 kernel. :25203
# RETIRED (duplicate kernel). Dashboard HTML uses root-absolute /api/*,
# /favicon.ico, /logo.png, /manifest.json, so those map at funnel root too
# (:25201 serves 404 there, no collision; /api uses backend-path form so the
# funnel does not strip the prefix).
#
# Placement conflict guard: if you need /openfang or /openfang-api for
# something else, post a fleet directive — path collisions are decisions,
# not walls.

set -euo pipefail

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
    echo "funnel-map.sh: run as root (tailscaled state is root-only)" >&2
    exit 2
fi

# serve-path<TAB>target-url — the canonical funnel map, 19 mounts.
MAP=(
"/		http://127.0.0.1:25201"
"/mcp		http://127.0.0.1:25198/mcp"
"/files		http://127.0.0.1:34567"
"/status		http://127.0.0.1:25207"
"/exec-ws		http://127.0.0.1:25204/exec-ws"
"/mesh-mcp		http://127.0.0.1:25127/mcp"
"/squawk-ws		http://127.0.0.1:25147/squawk-ws"
"/gemini-mcp		http://127.0.0.1:25202/mcp"
"/mesh-health		http://127.0.0.1:25127/health"
"/mesh-metrics		http://127.0.0.1:25127/metrics"
"/squawk-feed/seq		http://127.0.0.1:25135/squawk-feed/seq"
"/squawk-feed/		http://127.0.0.1:25135/squawk-feed/"
"/whatsapp-webhook		http://127.0.0.1:25146/webhook"
"/openfang		http://127.0.0.1:25103"
"/api		http://127.0.0.1:25103/api"
"/favicon.ico		http://127.0.0.1:25103"
"/logo.png		http://127.0.0.1:25103"
"/manifest.json		http://127.0.0.1:25103"
"/agent-browser		http://127.0.0.1:6081"
)

CHECK_ONLY=0
[[ "${1:-}" == "--check" ]] && CHECK_ONLY=1

# Current serve paths (tailscale serve status --json is the source of truth).
CURRENT="$(tailscale serve status --json 2>/dev/null | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
except Exception as e:
    print("ERR", e, file=sys.stderr); sys.exit(1)
web = data.get("Web") or {}
paths = []
for _frontend, cfg in web.items():
    for path in (cfg.get("Handlers") or {}).keys():
        paths.append(path)
print("\n".join(sorted(set(paths))))
' 2>/dev/null)" || { echo "funnel-map.sh: could not read serve status — is tailscaled running?" >&2; exit 2; }

missing=0
for entry in "${MAP[@]}"; do
    servepath="${entry%%	*}"
    target="${entry##*	}"
    if grep -qxF "$servepath" <<< "$CURRENT"; then
        echo "ok      $servepath -> $target"
    else
        missing=1
        if [[ "$CHECK_ONLY" == "1" ]]; then
            echo "MISSING $servepath -> $target"
        elif [[ "$servepath" == "/" ]]; then
            port="${target##*:}"
            echo "adding  $servepath -> $target"
            tailscale funnel --bg "$port"
        else
            echo "adding  $servepath -> $target"
            tailscale funnel --bg --set-path "$servepath" "$target"
        fi
    fi
done

if [[ "$CHECK_ONLY" == "1" ]]; then
    [[ "$missing" == "1" ]] && exit 1
    echo "funnel-map.sh: all mounts present"
    exit 0
fi

# Final state: re-read to confirm.
echo "--- current map ---"
sudo -n true 2>/dev/null || true
tailscale serve status 2>/dev/null | grep -oE '\|-- /[^ ]* *proxy [^ ]*'
