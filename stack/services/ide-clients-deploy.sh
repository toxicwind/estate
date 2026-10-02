#!/usr/bin/env bash
set -euo pipefail
export SOVEREIGN_ROOT="${SOVEREIGN_ROOT:-/home/toxic/estate}"
exec bun run "$SOVEREIGN_ROOT/src/deploy/ide_clients.ts"
