#!/usr/bin/env bash
set -euo pipefail
# squawk-feed launcher (pitchfork daemon).
# Token auto-configures server-side now (2026-09-21): squawk_feed.py resolves
# $SQUAWK_FEED_TOKEN > ~/.shingle/squawk-relay/feed-token > auto-generate.
# No manual token setup needed. Future keys go in
# ~/.shingle/squawk-relay/settings.conf (KEY=VALUE lines).
export FLEET_KEYS_DIR="/home/toxic/.shingle/squawk-root/keys"
exec python3 /home/toxic/sovereign/projects/range/ranch/squawk/squawk_feed.py --root /home/toxic/.shingle/squawk-root --channel fleet --bind 127.0.0.1 --port 25135 --identity relay
