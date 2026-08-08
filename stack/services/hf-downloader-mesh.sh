#!/usr/bin/env bash
set -euo pipefail
SOV="${SOVEREIGN_ROOT:-/home/toxic/sovereign}"
source "$SOV/stack/lib-ports.sh"
PORT="${HF_DOWNLOADER_PORT:?}"
BACKEND="${HF_DOWNLOADER_BACKEND_PORT:-25206}"

fuser -k "${PORT}/tcp" 2>/dev/null || true
fuser -k "${BACKEND}/tcp" 2>/dev/null || true

# Start HF downloader backend
/home/toxic/.local/bin/hfdownloader \
  --port "${BACKEND}" \
  --host 0.0.0.0 \
  --data-dir "$SOV/hf-downloader/data" &
HFD_PID=$!

cleanup() { kill "$HFD_PID" "$FRONT_PID" 2>/dev/null || true; }
trap cleanup EXIT

for i in $(seq 1 60); do
  curl -sf -m 0.5 "http://127.0.0.1:${BACKEND}/health" >/dev/null 2>&1 && break
  sleep 0.2
done

/home/toxic/.bun/bin/bun run "$SOV/src/services/mesh-front.ts" \
  --service hf-downloader \
  --listen "0.0.0.0:${PORT}" \
  --backend "127.0.0.1:${BACKEND}" &
FRONT_PID=$!

wait $FRONT_PID
