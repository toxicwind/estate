#!/usr/bin/env bash
set -euo pipefail
[ -f README.md ]  || { echo "FAIL: README.md missing" >&2; exit 1; }
[ -f .gitignore ] || { echo "FAIL: .gitignore missing" >&2; exit 1; }
if git ls-files | grep -q "\.estate/"; then echo "FAIL: .estate/ tracked" >&2; exit 1; fi
echo SMOKE_OK
exit 0
