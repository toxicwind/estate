#!/usr/bin/env bash
# Non-watch binary start (production-ish). Prefer rust-web-hot.sh for dev.
set -euo pipefail
SOV="${ESTATE_ROOT:-$PWD}"
# shellcheck source=../lib-ports.sh
source "$SOV/stack/lib-ports.sh"
# Backend binary binds the internal backend port; mesh-front proxies 25101→25201
RUST_WEB_PORT="${RUST_WEB_BACKEND_PORT:-25201}"
require_port RUST_WEB_PORT
require_port WATCHDOG_PORT
require_port HERD_PORT
export RUST_WEB_PORT WATCHDOG_PORT ESTATE_ROOT="$SOV"
export LLM_PROXY_URL="${LLM_PROXY_URL:-http://127.0.0.1:${HERD_PORT}}"

BIN=""
for cand in \
  "$SOV/bin/estate_web" \
  "$SOV/rust_algo_web/target/release/estate_web" \
  "$SOV/rust_algo_web/target/release/estate_devops_advisor"
do
  if [[ -x "$cand" ]]; then
    BIN="$(realpath "$cand")"
    break
  fi
done

if [[ -z "$BIN" ]]; then
  echo "[rust-web] building release..." >&2
  (cd "$SOV/rust_algo_web" && cargo build --release -q)
  BIN="$SOV/rust_algo_web/target/release/estate_web"
  [[ -x "$BIN" ]] || BIN="$SOV/rust_algo_web/target/release/estate_devops_advisor"
fi

[[ -x "$BIN" ]] || {
  echo "estate_web binary missing" >&2
  exit 1
}
export TERM=xterm-256color
cd "$SOV/rust_algo_web" && exec "$BIN"
