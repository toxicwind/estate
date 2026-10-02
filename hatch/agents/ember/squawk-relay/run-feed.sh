#!/usr/bin/env bash
set -euo pipefail
# squawk-feed launcher (pitchfork daemon).
# Token auto-configures server-side now (2026-09-21): squawk_feed.py resolves
# $SQUAWK_FEED_TOKEN > ~/.fleet-bus/squawk-relay/feed-token > auto-generate.
# No manual token setup needed. Future keys go in
# ~/.fleet-bus/squawk-root/keys/ (see FLEET_KEYS_DIR below).
#
# IDEMPOTENT (2026-09-29): if a healthy feed is already serving :25135,
# exit 0 immediately instead of crashing on EADDRINUSE. The pitchfork
# supervisor can spawn duplicate retries when its state desyncs (e.g. after
# `clean --daemon` leaks a retry task); duplicates must be quiet no-ops,
# not error loops.
if curl -sf --max-time 2 "http://127.0.0.1:25135/squawk-feed/seq" >/dev/null 2>&1; then
  exit 0
fi
export FLEET_KEYS_DIR="/home/toxic/.fleet-bus/squawk-root/keys"
exec python3 /home/toxic/estate/ranch/squawk/squawk_feed.py --root /home/toxic/.fleet-bus/squawk-root --channel fleet --bind 127.0.0.1 --port 25135 --identity relay
