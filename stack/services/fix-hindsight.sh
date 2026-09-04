#!/usr/bin/env bash
# Fix script for hindsight daemon - clears state and restarts with 25100 local provider
set -euo pipefail

echo "[fix-hindsight] Stopping any running hindsight..."
pitchfork stop hindsight 2>/dev/null || true
sleep 1

echo "[fix-hindsight] Cleaning docker container..."
docker rm -f hindsight 2>/dev/null || true

echo "[fix-hindsight] Clearing port conflicts..."
fuser -k 25117/tcp 2>/dev/null || true
fuser -k 25118/tcp 2>/dev/null || true

echo "[fix-hindsight] Restarting with local provider (25100)..."
export OPENAI_API_KEY=""
export HINDSIGHT_API_LLM_PROVIDER="local"
export HINDSIGHT_API_LLM_API_KEY="llama-swap-local-key"
export HINDSIGHT_API_LLM_API_URL="http://127.0.0.1:25100"
export HINDSIGHT_API_LLM_MODEL=""

pitchfork restart -q hindsight 2>&1
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
