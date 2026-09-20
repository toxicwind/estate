#!/bin/bash
# bidder-scout launcher - started by pitchfork
set -euo pipefail
exec python3 /home/toxic/sovereign/agents/oracle-market/bin/bidder.py \
  --id scout \
  --name Scout \
  --emoji "🔭" \
  --tags "probe,research,docs" \
  --tagline "I go first, look around, and report back. If it's unknown territory, I'm already halfway there!"
