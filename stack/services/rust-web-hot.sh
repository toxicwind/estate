#!/usr/bin/env bash
# Hot-reload rust dashboard + embedded watchdog (ports from .env.local / mise).
# SSOT: RUST_WEB_PORT=25101, WATCHDOG_PORT=25111 — never 25104 (ast-matrix).
set -euo pipefail
SOV="${SOVEREIGN_ROOT:-$PWD}"
export PATH="${HOME}/.cargo/bin:/usr/bin:/bin:${PATH}"
export RUST_WEB_PORT="${RUST_WEB_PORT:-25101}"
export LLM_PROXY_URL="${LLM_PROXY_URL:-http://127.0.0.1:25100}"
export WATCHDOG_PORT="${WATCHDOG_PORT:-25111}"
export SOVEREIGN_ROOT="$SOV"

cd "$SOV/rust_algo_web"

if ! command -v cargo-watch >/dev/null 2>&1; then
  echo "[rust-web-hot] installing cargo-watch..." >&2
  cargo install cargo-watch --locked 2>&1 | tail -5
fi

# Free stale binds (binary path only — no pkill -f self-match thrash)
fuser -k "${RUST_WEB_PORT}/tcp" 2>/dev/null || true
fuser -k "${WATCHDOG_PORT}/tcp" 2>/dev/null || true

echo "[rust-web-hot] cargo watch → :${RUST_WEB_PORT} watchdog :${WATCHDOG_PORT}" >&2
# Watch sources + Cargo.toml; release for hot-path perf while developing
exec cargo watch \
  -q \
  -c \
  -w src \
  -w Cargo.toml \
  -x 'run --release'
