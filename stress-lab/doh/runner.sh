#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")"
declare -a pids=() names=()
while IFS=$'\t' read -r name cmd match suite; do
  [ -z "$name" ] && continue
  names+=("$name")
  ( out=$(eval "$cmd" 2>"/tmp/err_${name}.$$"); rc=$?
    if grep -qF "$match" <<<"$out"; then echo "PASS $name ($suite)"
    else echo "FAIL $name ($suite) rc=$rc"; [ -s "/tmp/err_${name}.$$" ] && sed 's/^/    | /' "/tmp/err_${name}.$$" | head -5; fi
    rm -f "/tmp/err_${name}.$$" ) &
  pids+=("$!")
done < <(python3 parse_strategies.py strategies.json)
for p in "${pids[@]}"; do wait "$p"; done
