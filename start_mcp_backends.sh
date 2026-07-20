#!/bin/bash
# Start byte-vision-llamacpp (streamable-http :25120) and gibber-crypto (SSE :3006)
# as detached daemons so mcpproxy (external HTTP/SSE mode) can connect to them.
set -u

if ! ss -ltn 2>/dev/null | grep -q ':25120'; then
  echo "[start] launching byte-vision on :25120"
  setsid bash -c 'cd /home/toxic/byte-vision-mcp && exec /home/toxic/go/bin/byte-vision-mcp' >/home/toxic/byte-vision-mcp/byte-vision.log 2>&1 &
else
  echo "[start] byte-vision already listening on :25120"
fi

if ! ss -ltn 2>/dev/null | grep -q ':3006'; then
  echo "[start] launching gibber-crypto on :3006"
  setsid bash -c 'cd /home/toxic/mcp-installs/gibber-mcp && PORT=3006 exec node build/index.js' >/home/toxic/mcp-installs/gibber-mcp/gibber.log 2>&1 &
else
  echo "[start] gibber already listening on :3006"
fi

sleep 4
echo "=== after start ==="
ss -ltn 2>/dev/null | grep -E ':25120|:3006' && echo OK || echo "STILL DOWN"
