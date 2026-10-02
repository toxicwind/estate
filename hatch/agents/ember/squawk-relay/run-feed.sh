#!/usr/bin/env bash
set -euo pipefail
# squawk-feed launcher (pitchfork daemon).
# Token: squawk_feed.py requires $SQUAWK_FEED_TOKEN. The canonical token file is
# /home/toxic/.fleet-bus/squawk-relay/feed-token (same file fleet-ui.ts reads
# server-side). Export it here so pitchfork restarts work unattended.
# Future keys go in /home/toxic/.fleet-bus/squawk-root/keys/ (FLEET_KEYS_DIR).
#
# PATH-HARDENED (2026-10-02): absolute /usr/bin/python3. The pitchfork stanza
# sets mise=false, so mise shims are NOT on the supervisor PATH and bare
# `python3` dies with ENOENT ("No such file or directory") on DaemonStart.
#
# IDEMPOTENT (2026-09-29): if a healthy feed is already serving :25135,
# exit 0 immediately instead of crashing on EADDRINUSE. The pitchfork
# supervisor can spawn duplicate retries when its state desyncs (e.g. after
# `clean --daemon` leaks a retry task); duplicates must be quiet no-ops,
# not error loops.
if curl -sf --max-time 2 "http://127.0.0.1:25135/squawk-feed/seq" >/dev/null 2>&1; then
  exit 0
fi
FEED_TOKEN_FILE="/home/toxic/.fleet-bus/squawk-relay/feed-token"
if [ ! -r "$FEED_TOKEN_FILE" ]; then
  echo "squawk-feed launcher: token file unreadable: $FEED_TOKEN_FILE" >&2
  exit 2
fi
export SQUAWK_FEED_TOKEN="$(cat "$FEED_TOKEN_FILE")"
export FLEET_KEYS_DIR="/home/toxic/.fleet-bus/squawk-root/keys"
exec /usr/bin/python3 /home/toxic/estate/ranch/squawk/squawk_feed.py --root /home/toxic/.fleet-bus/squawk-root --channel fleet --bind 127.0.0.1 --port 25135 --identity relay
