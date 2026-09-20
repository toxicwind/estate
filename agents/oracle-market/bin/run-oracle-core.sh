#!/bin/bash
# oracle-core daemon entrypoint - started by pitchfork (sovereign/oracle-core)
set -euo pipefail
exec python3 /home/toxic/sovereign/agents/oracle-market/bin/oracle_daemon.py
