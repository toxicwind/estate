#!/usr/bin/env bash
set -euo pipefail
SOV="${SOVEREIGN_ROOT:-$PWD}"
# Canonical ports: llama-swap :25100, dashboard :25101, watchdog :25104
export RUST_WEB_PORT="${RUST_WEB_PORT:-25101}"
export LLM_PROXY_URL="${LLM_PROXY_URL:-http://127.0.0.1:25100}"
export WATCHDOG_PORT="${WATCHDOG_PORT:-25104}"

BIN=""
for cand in \
  "$SOV/bin/sovereign_web" \
  "$SOV/rust_algo_web/target/release/sovereign_web" \
  "$SOV/rust_algo_web/target/release/sovereign_devops_advisor" \
  "$SOV/backup/clean_2026-07-11_prod/trees/rust_algo_web/target/release/sovereign_web"
do
  if [[ -x "$cand" ]]; then
    BIN="$(realpath "$cand")"
    break
  fi
done

if [[ -z "$BIN" ]]; then
  if [[ -f "$SOV/rust_algo_web/Cargo.toml" ]]; then
    echo "[rust-web] building release..." >&2
    (cd "$SOV/rust_algo_web" && cargo build --release -q)
    BIN="$SOV/rust_algo_web/target/release/sovereign_web"
    [[ -x "$BIN" ]] || BIN="$SOV/rust_algo_web/target/release/sovereign_devops_advisor"
    # install thin copy for next start
    if [[ -x "$BIN" ]]; then
      install -m 0755 "$BIN" "$SOV/bin/sovereign_web"
      BIN="$SOV/bin/sovereign_web"
    fi
  fi
fi

[[ -x "$BIN" ]] || { echo "[rust-web] binary missing (bin/sovereign_web or rust_algo_web)" >&2; exit 1; }

pkill -f "sovereign_web|sovereign_devops_advisor" 2>/dev/null || true
fuser -k "${RUST_WEB_PORT}/tcp" 2>/dev/null || true
fuser -k "${WATCHDOG_PORT}/tcp" 2>/dev/null || true
echo "[rust-web] exec $BIN :${RUST_WEB_PORT}/wd:${WATCHDOG_PORT}"
exec "$BIN"
