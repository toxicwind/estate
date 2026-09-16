#!/usr/bin/env bash
# Hot-reload rust dashboard on backend port + mesh-front on public RUST_WEB_PORT
set -euo pipefail
SOV="${SOVEREIGN_ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}"
export PATH="${HOME}/.cargo/bin:/usr/bin:/bin:${PATH}"
source "$SOV/stack/lib-ports.sh"
require_env RUST_WEB_PORT
require_env WATCHDOG_PORT
require_env LLAMA_SWAP_PORT
PUBLIC="${RUST_WEB_PORT}"
BACKEND="${RUST_WEB_BACKEND_PORT:-25201}"
export RUST_WEB_PORT="${BACKEND}"
export WATCHDOG_PORT SOVEREIGN_ROOT="$SOV"
export LLM_PROXY_URL="${LLM_PROXY_URL:-http://127.0.0.1:${LLAMA_SWAP_PORT}}"

cd "$SOV/rust_algo_web"
if ! command -v cargo-watch >/dev/null 2>&1; then
  cargo install cargo-watch --locked 2>&1 | tail -5
fi
fuser -k "${PUBLIC}/tcp" 2>/dev/null || true
fuser -k "${BACKEND}/tcp" 2>/dev/null || true
fuser -k "${WATCHDOG_PORT}/tcp" 2>/dev/null || true
export TERM="${TERM:-xterm-256color}"
export CARGO_TERM_COLOR="${CARGO_TERM_COLOR:-always}"
if command -v sccache >/dev/null 2>&1; then
  export RUSTC_WRAPPER="${RUSTC_WRAPPER:-sccache}"
fi
echo "[rust-web-hot] backend :${BACKEND} mesh-front :${PUBLIC}" >&2

cargo watch -q -w src -w Cargo.toml -x 'run --release' &
CARGO_PID=$!
cleanup() { kill "$CARGO_PID" 2>/dev/null || true; }
trap cleanup EXIT

for i in $(seq 1 120); do
  curl -sf -m 0.5 "http://127.0.0.1:${BACKEND}/health" >/dev/null 2>&1 && break
  sleep 0.5
done

exec /home/toxic/.bun/bin/bun --hot run "$SOV/src/services/mesh-front.ts" \
  --service rust-web \
  --listen "0.0.0.0:${PUBLIC}" \
  --backend "127.0.0.1:${BACKEND}"
