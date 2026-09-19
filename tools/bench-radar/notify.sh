#!/usr/bin/env bash
# BENCH-RADAR notify hook — fired once per NEW (non-backfill) regression event.
# $1 = event JSON. The lane wires fleet delivery here; default is durable logging
# plus a best-effort fleet-chat post (env-gated, never fatal).
#
# Env:
#   FLEET_CHAT_URL        default http://127.0.0.1:25122
#   BENCH_RADAR_ROOM      fleet-chat room to post to (default: ops)
#   BENCH_RADAR_AGENT_ID  agent_id for fleet-chat (default: bench-radar)
set -u
EVENT="${1:-{}}"
HERE="$(cd "$(dirname "$0")" && pwd)"
LOG="$HERE/state/alerts.log"

sev="$(printf '%s' "$EVENT" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("severity","?"))' 2>/dev/null || echo '?')"
suite="$(printf '%s' "$EVENT" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("suite","?"))' 2>/dev/null || echo '?')"
rule="$(printf '%s' "$EVENT" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("rule","?"))' 2>/dev/null || echo '?')"
ev="$(printf '%s' "$EVENT" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("evidence",""))' 2>/dev/null || echo '')"

line="$(date -u +%FT%TZ) [$sev] bench-radar/$suite $rule :: $ev"
printf '%s\n' "$line" >> "$LOG"

# best-effort fleet-chat post (lane-wirable room); silent on failure
FLEET_CHAT_URL="${FLEET_CHAT_URL:-http://127.0.0.1:25122}"
ROOM="${BENCH_RADAR_ROOM:-ops}"
AGENT="${BENCH_RADAR_AGENT_ID:-bench-radar}"
if [ -n "${ROOM}" ]; then
  body="🧊 BENCH-RADAR [$sev] $suite :: $rule — $ev"
  python3 - "$FLEET_CHAT_URL" "$ROOM" "$AGENT" "$body" <<'EOF' >/dev/null 2>&1 || true
import json, sys, urllib.request
url, room, agent, body = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
req = urllib.request.Request(
    f"{url}/v1/rooms/{room}/messages",
    data=json.dumps({"agent_id": agent, "body": body}).encode(),
    headers={"content-type": "application/json"}, method="POST")
try:
    urllib.request.urlopen(req, timeout=5)
except Exception:
    pass
EOF
fi
exit 0
