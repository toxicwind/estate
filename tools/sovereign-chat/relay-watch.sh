#!/usr/bin/env bash
# relay-watch.sh — outbound leg of the #relay (WhatsApp) bridge.
# Polls sovereign-chat /v1/state for new decision-kind messages since the
# durable watermark and prints them for the relay agent. Prints QUIET when
# there is nothing new (the relay agent then stays silent).
#
# Loop guard: skips messages from the relay agent itself — inbound
# WhatsApp->fleet relays never bounce back to WhatsApp.
#
# Watermark discipline: this script NEVER advances the watermark. It reports
# CANDIDATE=<max seq seen>. The relay agent advances the watermark file only
# AFTER the WhatsApp message is actually delivered. Duplicate-on-failure beats
# loss-on-failure: a re-report is visible (seq numbers), a lost decision is not.
#
# Watermark lives in the server state dir (durable on awrawr-pc, not the cell).
# Edge: decisions list is capped at 50; a >50-decision burst inside one poll
# interval would clip. Poll interval is 5 min — bursts that large get a
# follow-up sweep via /v1/rooms/<room>/messages instead.
set -u

STATE_DIR="${SOVEREIGN_CHAT_STATE_DIR:-/home/toxic/sovereign/tools/sovereign-chat/state}"
WM="$STATE_DIR/relay-watermark"
TOKEN_FILE="${SOVEREIGN_CHAT_TOKEN_FILE:-/home/toxic/.config/sovereign-chat-token}"
BASE="${SOVEREIGN_CHAT_BASE:-http://127.0.0.1:25120}"
RELAY_AGENT="${RELAY_AGENT_ID:-20260918-whatsapp-d0d198ad}"

last=0
[ -f "$WM" ] && last="$(tr -dc '0-9' < "$WM" 2>/dev/null || echo 0)"
[ -z "$last" ] && last=0

T="$(cat "$TOKEN_FILE" 2>/dev/null)" || { echo "WATCH_ERROR cannot read token file"; exit 1; }
[ -n "$T" ] || { echo "WATCH_ERROR empty token"; exit 1; }

state="$(curl -s -m 10 -H "Authorization: Bearer $T" "$BASE/v1/state")" || { echo "WATCH_ERROR state fetch failed"; exit 1; }

new="$(printf '%s' "$state" | python3 -c "
import json, sys
try:
    d = json.loads(sys.stdin.read())['state']
except Exception as e:
    print('WATCH_ERROR bad state JSON: ' + str(e), file=sys.stderr)
    sys.exit(1)
last = int(sys.argv[1]); me = sys.argv[2]
for m in d.get('decisions', []):
    if m.get('seq', 0) > last and m.get('from_agent') != me:
        print(json.dumps(m))
" "$last" "$RELAY_AGENT")"

if [ -z "$new" ]; then echo "QUIET"; exit 0; fi
printf '%s\n' "$new"
max="$(printf '%s\n' "$new" | python3 -c "import json,sys; print(max(json.loads(l)['seq'] for l in sys.stdin))")"
echo "CANDIDATE=$max"
echo "NOTE: advance watermark to $max only after the WhatsApp relay is delivered."
