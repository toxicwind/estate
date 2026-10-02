#!/usr/bin/env bash
set -euo pipefail
exec bun run "${SOVEREIGN_ROOT:-/home/toxic/estate}/src/deploy/code_insiders.ts"
