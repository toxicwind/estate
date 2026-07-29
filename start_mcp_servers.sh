#!/bin/bash
# Start MCP stack via pitchfork (no sleep, no orphans)
set -euo pipefail
cd "$(dirname "$0")"

echo "=== Starting MCP Servers ==="

# Start all core daemons (idempotent — pitchfork skips already-running)
pitchfork start --group core

echo ""
echo "=== Health Checks ==="
for svc in mcpproxy byte-vision-proxy; do
  port=$(pitchfork daemons 2>/dev/null | grep "$svc" | head -1 && true)
done

for p in 25109 25120; do
  label="mcpproxy"
  [[ "$p" == "25120" ]] && label="MCP gateway"
  status=$(curl -sf -m 3 "http://127.0.0.1:$p/health" 2>/dev/null || echo "unavailable")
  echo "$label ($p): $status"
done

echo ""
echo "=== All Daemons ==="
pitchfork list
