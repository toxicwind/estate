#!/usr/bin/env bash
# Non-watch binary start (production-ish). Prefer rust-web-hot.sh for dev.
set -euo pipefail
SOV="${SOVEREIGN_ROOT:-$PWD}"
# shellcheck source=../lib-ports.sh
source "$SOV/stack/lib-ports.sh"
require_env RUST_WEB_PORT
require_env WATCHDOG_PORT
require_env LLAMA_SWAP_PORT
export RUST_WEB_PORT WATCHDOG_PORT SOVEREIGN_ROOT="$SOV"
export LLM_PROXY_URL="${LLM_PROXY_URL:-http://127.0.0.1:${LLAMA_SWAP_PORT}}"

BIN=""
for cand in \
  "$SOV/bin/sovereign_web" \
  "$SOV/rust_algo_web/target/release/sovereign_web" \
  "$SOV/rust_algo_web/target/release/sovereign_devops_advisor"
do
  if [[ -x "$cand" ]]; then
    BIN="$(realpath "$cand")"
    break
  fi
done

if [[ -z "$BIN" ]]; then
  echo "[rust-web] building release..." >&2
  (cd "$SOV/rust_algo_web" && cargo build --release -q)
  BIN="$SOV/rust_algo_web/target/release/sovereign_web"
  [[ -x "$BIN" ]] || BIN="$SOV/rust_algo_web/target/release/sovereign_devops_advisor"
fi

[[ -x "$BIN" ]] || {
  echo "sovereign_web binary missing" >&2
  exit 1
}
exec "$BIN"
