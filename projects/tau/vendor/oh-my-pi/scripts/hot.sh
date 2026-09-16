#!/usr/bin/env bash
# Inner-loop dev runner.
#   - Rust: cargo-watch rebuilds pi-natives on any crates/** change
#   - Napi: re-embeds the .node into packages/natives/native/
#   - JS  : bun --hot reloads coding-agent on any packages/** change
#   - Seam: touches a restart sentinel when the .node changes; bun wrapper reads it
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
ENGINE="$PWD"

export CARGO_TARGET_DIR="${CARGO_TARGET_DIR:-$HOME/.cargo-target}"
export CARGO_INCREMENTAL=1
export RUSTC_WRAPPER=sccache
mkdir -p "$CARGO_TARGET_DIR"

say(){ printf '\033[1;35m[hot]\033[0m %s\n' "$*"; }

# ---- pid juggling -----------------------------------------------------
PIDS=()
trap 'say "shutting down"; for p in "${PIDS[@]}"; do kill "$p" 2>/dev/null; done; exit 0' INT TERM

# ---- rust watcher -----------------------------------------------------
say "starting cargo-watch on crates/"
(
  cargo watch \
    --watch crates \
    --ignore 'crates/*/target' \
    --ignore 'crates/*/*.reconcile-bak-*' \
    -s '
      set -e
      cargo build --profile dev -p pi-natives 2>&1 | tail -20
      bun packages/natives/scripts/build-bindings.ts 2>/dev/null || \
        bun ../../scripts/bazel-natives.ts host --dest native 2>/dev/null || true
      touch packages/natives/native/.hot-reload-sentinel
    '
) &
PIDS+=($!)

# ---- js watcher -------------------------------------------------------
say "starting bun --hot on coding-agent"
(
  SOVEREIGN_HOME="$ENGINE/.." \
  PI_CONFIG_DIR="$HOME/.tau" \
  PI_CODING_AGENT_DIR="$HOME/.tau/agent" \
  exec bun --hot "$ENGINE/packages/coding-agent/src/cli.ts" -- "$@"
) &
PIDS+=($!)

wait
