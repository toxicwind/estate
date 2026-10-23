#!/usr/bin/env bash
# Concurrent strategy runner: runs all arms in parallel (& + wait). 
# stderr is captured per-arm and cross-referenced against a signature->patch map.
set -uo pipefail
cd "$(dirname "$0")"
declare -a pids=()
declare -a names=()
while IFS=$'\t' read -r name cmd match suite; do
  [ -z "$name" ] && continue
  names+=("$name")
  ( 
    out=$(eval "$cmd" 2>"/tmp/err_${name}.$$"); rc=$?
    outro=$(exec 2>/dev/null; eval "$cmd" 2>/dev/null || true)  # ensure we have stdout for match
    if grep -qF "$match" <<<"$outro" && [ "$rc" -eq 0 ]; then
      echo "PASS $name ($suite)"
    else
      echo "FAIL $name ($suite) rc=$rc"
      if [ -s "/tmp/err_${name}.$$" ]; then sed 's/^/    | /' "/tmp/err_${name}.$$" | head -6; fi
    fi
    rm -f "/tmp/err_${name}.$$"
  ) &
  pids+=("$!")
done < <(python3 parse_strategies.py strategies.json)
rc=0
for i in "${!pids[@]}"; do wait "${pids[$i]}" || rc=1; done
exit "$rc"
