#!/usr/bin/env bash
# Fix script for hindsight daemon - clears state and restarts with rhodochrosite :25193 provider
set -euo pipefail

echo "[fix-hindsight] Stopping any running hindsight..."
pitchfork stop hindsight 2>/dev/null || true
sleep 1

echo "[fix-hindsight] Cleaning docker container..."
docker rm -f hindsight 2>/dev/null || true

echo "[fix-hindsight] Clearing port conflicts..."
fuser -k 25117/tcp 2>/dev/null || true
fuser -k 25118/tcp 2>/dev/null || true

echo "[fix-hindsight] Ensuring rhodochrosite (25193) is running..."
if ! curl -sf -m 2 http://127.0.0.1:25193/health >/dev/null 2>&1; then
    echo "[fix-hindsight] Starting bornite..."
    ESTATE_ROOT=/home/toxic/pens/estate bash /home/toxic/pens/estate/stack/services/bornite.sh &
    sleep 2
fi

echo "[fix-hindsight] Restarting hindsight with openai/gpt-oss-20b via rhodochrosite (25193)..."
export HINDSIGHT_API_LLM_PROVIDER="openai"
export HINDSIGHT_API_LLM_API_KEY="$(cat /home/toxic/.rhodochrosite-data/client-key.corral 2>/dev/null)"
export HINDSIGHT_API_LLM_BASE_URL="http://127.0.0.1:25193/v1"
export HINDSIGHT_API_LLM_MODEL="openai/gpt-oss-20b"

(cd /home/toxic/pens/estate && ./stack/services/hindsight.sh) &
echo "[fix-hindsight] Waiting 15s for startup..."
sleep 15

echo "[fix-hindsight] Checking health endpoints..."
if curl -sf -m 3 http://127.0.0.1:25117/health >/dev/null 2>&1; then
    echo "[fix-hindsight] ✅ API (25117) healthy"
else
    echo "[fix-hindsight] ❌ API (25117) unhealthy"
fi

if curl -sf -m 3 http://127.0.0.1:25118/health >/dev/null 2>&1; then
    echo "[fix-hindsight] ✅ Control Plane (25118) healthy"
else
    echo "[fix-hindsight] ❌ Control Plane (25118) unhealthy"
fi

echo "[fix-hindsight] Pitchfork status:"
pitchfork status hindsight 2>&1
