#!/bin/bash
# L7: companion binaries + launcher scripts — who sets what, when.
set -u
OUT=../findings/lane7_companions.txt
{
echo "== spawnd: JARVIS refs =="
grep -a -o -E '.{0,60}JARVIS_[A-Z_0-9]+.{0,40}' /opt/hatch/bin/spawnd | head -30
echo; echo "== spawnd file =="; file /opt/hatch/bin/spawnd; ls -la /opt/hatch/bin/spawnd
echo; echo "== JARVIS ref counts in other companions =="
for b in hatch-doctor hatch-healthd hatch-multicall hatch-execd hatch-rescue; do
  c=$(grep -a -o 'JARVIS_[A-Z_0-9]*' /opt/hatch/bin/$b 2>&1 | grep -c JARVIS)
  echo "$b: $c"
done
echo; echo "== launch-daemon.sh =="; cat /opt/hatch/runtime-cell/launch-daemon.sh
echo; echo "== run-daemon.sh =="; cat /opt/hatch/runtime-cell/run-daemon.sh
echo; echo "== guest-runtime-env.sh =="; cat /opt/hatch/runtime-cell/guest-runtime-env.sh
} > "$OUT" 2>&1
wc -l "$OUT"
