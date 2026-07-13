#!/usr/bin/env bash
set -euo pipefail
exec bun run "${SOVEREIGN_ROOT:-$HOME/sovereign}/src/deploy/code_insiders.ts"
