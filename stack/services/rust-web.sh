#!/usr/bin/env bash
set -euo pipefail
SOV="${SOVEREIGN_ROOT:-/home/toxic/sovereign}"
cd "$SOV/rust_algo_web"
export RUST_WEB_PORT="${RUST_WEB_PORT:-25005}"
export LLM_PROXY_URL="${LLM_PROXY_URL:-http://127.0.0.1:28080}"
BIN="./target/release/sovereign_devops_advisor"

# Kill stale instance so we don't get "Address already in use"
pkill -f "$BIN" >/dev/null 2>&1 || true
# Also free the port directly if something else is squatting on it
if command -v fuser >/dev/null 2>&1; then
    fuser -k "${RUST_WEB_PORT}/tcp" >/dev/null 2>&1 || true
fi

# Build only if missing or source is newer
if [[ ! -x "$BIN" ]] || [[ "$BIN" -ot src/ ]]; then
    cargo build --release -q
fi

exec "$BIN"