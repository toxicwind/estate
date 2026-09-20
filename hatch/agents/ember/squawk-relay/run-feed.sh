#!/usr/bin/env bash
set -euo pipefail
export SQUAWK_FEED_TOKEN="$(cat /home/toxic/.shingle/squawk-relay/feed-token)"
export FLEET_KEYS_DIR="/home/toxic/.shingle/squawk-root/keys"
exec python3 /home/toxic/squawk/squawk_feed.py --root /home/toxic/.shingle/squawk-root --channel fleet --bind 127.0.0.1 --port 25135 --identity relay
