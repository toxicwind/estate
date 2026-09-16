#!/usr/bin/env bash
# byte-vision service — Sovereign stack
set -euo pipefail
SOV="${SOVEREIGN_ROOT:-$HOME/sovereign}"
source "$SOV/stack/lib-ports.sh" 2>/dev/null || true
PORT="${BYTE_VISION_PORT:-25121}"

fuser -k "${PORT}/tcp" 2>/dev/null || true

exec "$SOV/tools/byte-vision-mock.sh"
