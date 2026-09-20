#!/bin/bash
# market-watchdog launcher - started by pitchfork
set -euo pipefail
exec python3 /home/toxic/sovereign/agents/oracle-market/bin/market_watchdog.py
