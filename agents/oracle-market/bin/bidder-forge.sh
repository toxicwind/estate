#!/bin/bash
# bidder-forge launcher - started by pitchfork
set -euo pipefail
exec python3 /home/toxic/sovereign/agents/oracle-market/bin/bidder.py \
  --id forge \
  --name Forge \
  --emoji "🔨" \
  --tags "code-fix,probe" \
  --tagline "I fix broken things and poke them till they confess. Point me at what's busted."
