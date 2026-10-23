#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
out=$(./poc_token_walk.mjs 2>&1); rc=$?
if [ $rc -eq 0 ] && grep -q 'Global maxP' <<<"$out"; then echo "tokwalk_ok linear"; exit 0; else echo "tokwalk_fail linear" >&2; echo "$out" >&2; exit 1; fi
