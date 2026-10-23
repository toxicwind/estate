#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
./poc_token_walk.mjs >/dev/null 2>&1
grep -q '__PSEUDO_SLOT4__' walk_data.json && { echo "tokwalk_ok pseudo"; exit 0; } || { echo "tokwalk_fail pseudo" >&2; exit 1; }
