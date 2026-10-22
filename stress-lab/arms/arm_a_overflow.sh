#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
out=$(python3 lib/sock_stress.py 2>&1); rc=$?
if [ $rc -eq 0 ] && grep -q "\"a-overflow\"" <<<"$out" && python3 -c "import json,sys; v=json.load(sys.stdin)['verdicts']; sys.exit(0 if v['a-overflow']['ok'] else 1)" <<<"$out"; then
  echo "sock_ok a_overflow"; exit 0
else
  echo "sock_fail a_overflow" >&2; echo "$out" >&2; exit 1
fi
