#!/usr/bin/env bash
set -euo pipefail
SOV="${SOVEREIGN_ROOT:-/home/toxic/sovereign}"
cd "$SOV/rust_algo_web"
export RUST_WEB_PORT="${RUST_WEB_PORT:-25005}"
export LLM_PROXY_URL="${LLM_PROXY_URL:-http://127.0.0.1:25021}"
BIN="./target/release/sovereign_devops_advisor"
if [[ -x "$BIN" ]] && "$BIN" --help >/dev/null 2>&1 || ldd "$BIN" 2>/dev/null | grep -q '/lib/ld-linux'; then
  exec "$BIN" 2>/dev/null || true
fi
cargo build --release -q
exec "$BIN"