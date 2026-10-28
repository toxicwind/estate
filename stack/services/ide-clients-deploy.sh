#!/usr/bin/env bash
set -euo pipefail
export ESTATE_ROOT="${ESTATE_ROOT:-/home/toxic/pens/estate}"
exec bun run "$ESTATE_ROOT/src/deploy/ide_clients.ts"
