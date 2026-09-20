#!/bin/bash
# run-auctioneer.sh: pitchfork launcher for the market auctioneer daemon.
set -euo pipefail
export SQUAWK_CHAT_ROOT="${SQUAWK_CHAT_ROOT:-/home/toxic/.shingle/squawk-root}"
export SQUAWK_CODE_DIR="${SQUAWK_CODE_DIR:-/home/toxic/sovereign/hatch/agents/ember/chat}"
export FLEET_KEYS_DIR="${FLEET_KEYS_DIR:-$SQUAWK_CHAT_ROOT/keys}"
exec python3 /home/toxic/sovereign/killer-features/bid-market/auctioneer.py
