#!/usr/bin/env bash
# feedlot service — Estate stack (real llama.cpp MCP, Go binary)
set -euo pipefail
SOV="${ESTATE_ROOT:-/home/toxic/pens/estate}"
source "$SOV/stack/lib-ports.sh" 2>/dev/null || true
PORT="${FEEDLOT_PORT:-25121}"

fuser -k "${PORT}/tcp" 2>/dev/null || true

CFG_DIR=/home/toxic/.config/feedlot
# Sync port into the Go app's config file
sed -i "s|^HttpPort=.*|HttpPort=:${PORT}|" "$CFG_DIR/feedlot-cfg.env"

cd "$CFG_DIR"
exec /home/toxic/.local/bin/feedlot-mcp
