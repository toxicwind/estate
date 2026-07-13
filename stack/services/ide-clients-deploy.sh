#!/usr/bin/env bash
set -euo pipefail
export SOVEREIGN_ROOT="${SOVEREIGN_ROOT:-$HOME/sovereign}"
exec bun run "$SOVEREIGN_ROOT/src/deploy/ide_clients.ts"
