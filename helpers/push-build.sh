#!/usr/bin/env bash
# Build Tau after a push using the repository's mise toolchain.
#
# The old script wrote JSON into $HOME/brand/queue for buildsrv/flicker. Build
# ownership is now local: `mise exec` resolves the declared tools and mbx-cache
# restores eligible task artifacts at :25148.
set -euo pipefail

TAU_ROOT="${TAU_HOME:-$HOME/tau}"
[[ -f "$TAU_ROOT/packages/coding-agent/package.json" ]] || {
  echo "tau checkout missing: $TAU_ROOT" >&2
  exit 66
}

cd "$TAU_ROOT/packages/coding-agent"
mise exec -- bun install
exec mise exec -- bun run build