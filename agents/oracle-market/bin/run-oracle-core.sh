#!/bin/bash
# oracle-core daemon entrypoint - started by pitchfork (estate/oracle-core)
set -euo pipefail
exec python3 /home/toxic/estate/agents/oracle-market/bin/oracle_daemon.py
