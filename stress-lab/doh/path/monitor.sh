#!/usr/bin/env bash
# Emergent DoH differential watchdog: continuous cell-side DNS-transparency monitor.
# Loops the probe, keeps a rolling verdict, and writes monitor_state.json the cell's VJ reads.
# Run under pitchfork/supervisord (loop); safe to ctrl-c.
set -uo pipefail
cd "$(dirname "$0")/.."
STATE=monitor_state.json
samples=0; glitches=0; last="STABLE"; since=""
trap 'echo "monitor stopped: $samples runs, $glitches glitch(es)"' EXIT
while true; do
  out=$(python3 doh_probe.py github.com A 2>/dev/null || true)
  now=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  vj=$(printf '%s' "$out" | python3 -c "import json,sys;
try: d=json.load(sys.stdin); print(d.get('vjTrigger','STABLE'))
except: print('ERR')" 2>/dev/null || echo STABLE)
  samples=$((samples+1))
  if [ "$vj" = "GLITCH" ]; then glitches=$((glitches+1)); last="GLITCH"; since="$now"; else last="STABLE"; fi
  cat > "$STATE" <<JSON
{"monitor":"doh-watchdog","samples":$samples,"glitches":$glitches,"last":"$last","last_glitch_at":"$since","ts":"$now"}
JSON
  sleep 30
done
