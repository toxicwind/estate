#!/usr/bin/env bash
set -euo pipefail
PORT="${BYTE_VISION_PORT:-25121}"

# byte-vision-mcp is an MCP server, it serves /mcp-completion
# Use the MCP initialize method as health check
for i in $(seq 1 60); do
  if curl -sf -m 1 -X POST "http://127.0.0.1:${PORT}/mcp-completion" \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"health-check","version":"1"}},"id":1}' \
    >/dev/null 2>&1; then
    echo "OK"
    exit 0
  fi
  sleep 0.5
done

echo "FAILED"
exit 1
