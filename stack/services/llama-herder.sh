#!/usr/bin/env bash
set -euo pipefail

SOV="${SOVEREIGN_ROOT:-/home/toxic/sovereign}"
PORT="${LLAMA_HERDER_PORT:-28080}"

# Binary resolution (symlink → project build → fallback)
BIN_CANDIDATES=(
    "${SOV}/tools/llama-swap/llama-swap"
    "${HOME}/.local/bin/llama-swap"
    "/home/toxic/projects/llama-swap-main/llama-swap"
)
BIN=""
for c in "${BIN_CANDIDATES[@]}"; do
    [[ -x "$c" ]] && { BIN="$(realpath "$c")"; break; }
done
[[ -n "$BIN" ]] || { echo "llama-swap binary not found" >&2; exit 1; }

# Config resolution (must be outside ignored tools/ folder)
CONF_CANDIDATES=(
    "${HOME}/.config/llama-swap/config.yaml"
    "${SOV}/config/llama-swap.yaml"
    "${SOV}/tools/llama-swap/config.yaml"
)
CONF=""
for c in "${CONF_CANDIDATES[@]}"; do
    [[ -f "$c" ]] && { CONF="$(realpath "$c")"; break; }
done
[[ -n "$CONF" ]] || { echo "config.yaml not found" >&2; exit 1; }

# Collision guard
START_PORT="$(grep -E '^\s*startPort:\s*[0-9]+' "$CONF" | grep -oE '[0-9]+' | head -1 || echo 25001)"
MODEL_COUNT="$(grep -cE '^\s{2}"[^"]+":' "$CONF" 2>/dev/null || grep -cE '^\s{2}[a-z_]+/[a-z0-9_-]+:' "$CONF" || echo 30)"
END_PORT=$((START_PORT + MODEL_COUNT + 10))

if (( PORT >= START_PORT && PORT <= END_PORT )); then
    echo "ERROR: PORT $PORT collides with backend range $START_PORT-$END_PORT" >&2
    exit 1
fi

# Port cleanup
if command -v fuser >/dev/null 2>&1; then
    fuser -k "${PORT}/tcp" 2>/dev/null || true
else
    lsof -ti tcp:"$PORT" 2>/dev/null | xargs -r kill -9 || true
fi

# Warmup (background, self-exiting)
(
    for _ in {1..60}; do
        curl -sf --max-time 1 "http://127.0.0.1:${PORT}/health" >/dev/null && break
        sleep 1
    done
    curl -sf --max-time 120 "http://127.0.0.1:${PORT}/v1/chat/completions" \
        -H 'Content-Type: application/json' \
        -d '{"model":"beellama/qwen-flash","messages":[{"role":"user","content":"ok"}],"max_tokens":1}' \
        >/dev/null 2>&1 || true
) & disown

echo "[llama-swap] BIN=$BIN CONF=$CONF PORT=$PORT"
exec "$BIN" --config "$CONF" --listen "127.0.0.1:${PORT}"