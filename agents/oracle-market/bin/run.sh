#!/bin/bash
# oracle-market daemon entrypoint - started by pitchfork
set -euo pipefail
exec python3 /home/toxic/sovereign/agents/oracle-market/bin/oracle_loop.py
