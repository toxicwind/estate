#!/usr/bin/env bash
# freeinference-provider-probe.sh — live UA/concurrency policy probes (2026-10-19).
# Companion to estate/docs/freeinference-provider.md. Keyring-sourced key, never echoed.
# Usage: bash estate/docs/probes/freeinference-provider-probe.sh
set -uo pipefail

KEY=$(grep "FREEINFERENCE" /home/toxic/.secrets | cut -d= -f2)
: "${FREEINFERENCE_API_KEY:=$KEY}"
UA_HONEST="tau/18.8.4 (+https://github.com/toxicwind/tau)"
UA_SPOOF='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
BASE=https://freeinference.org/v1

probe() { curl -s --max-time 10 -o /dev/null -w "%{http_code}" "$@"; }

echo "== P1-P4: UA matrix on GET /v1/models =="
echo "P1 honest tau UA           : $(probe -H "Authorization: Bearer $FREEINFERENCE_API_KEY" -H "User-Agent: $UA_HONEST" $BASE/models)  (want 200)"
echo "P2 chrome-spoof UA         : $(probe -H "Authorization: Bearer $FREEINFERENCE_API_KEY" -H "User-Agent: $UA_SPOOF" $BASE/models)  (200 = no UA gate today)"
echo "P3 empty UA                : $(probe -H "Authorization: Bearer $FREEINFERENCE_API_KEY" -H "User-Agent:" $BASE/models)  (200)"
echo "P4 curl default, no auth   : $(probe $BASE/models)  (200 = models list is public)"

echo "== P5-P7: UA matrix on POST /v1/chat/completions =="
body='{"model":"glm-5.3-flash","messages":[{"role":"user","content":"say ok"}],"max_tokens":3}'
echo "P5 honest UA  chat        : $(curl -s --max-time 20 -o /dev/null -w '%{http_code}' -H 'Content-Type: application/json' -H "Authorization: Bearer $FREEINFERENCE_API_KEY" -H "User-Agent: $UA_HONEST" -d "$body" $BASE/chat/completions)  (want 200)"
echo "P6 chrome-spoof chat      : $(curl -s --max-time 20 -o /dev/null -w '%{http_code}' -H 'Content-Type: application/json' -H "Authorization: Bearer $FREEINFERENCE_API_KEY" -H "User-Agent: $UA_SPOOF" -d "$body" $BASE/chat/completions)  (200)"
echo "P7 empty UA chat          : $(curl -s --max-time 20 -o /dev/null -w '%{http_code}' -H 'Content-Type: application/json' -H "Authorization: Bearer $FREEINFERENCE_API_KEY" -H 'User-Agent:' -d "$body" $BASE/chat/completions)  (200)"

echo "== P8: 2-slot concurrency (4 parallel chats; expect exactly 2x200 + 2x429) =="
for i in 1 2 3 4; do
  ( t0=$(date +%s.%N); code=$(curl -s --max-time 30 -o /dev/null -w '%{http_code}' -H 'Content-Type: application/json' -H "Authorization: Bearer $FREEINFERENCE_API_KEY" -H "User-Agent: $UA_HONEST" -d "$body" $BASE/chat/completions); t1=$(date +%s.%N); echo "req$i: $code $(echo "$t1 - $t0" | bc)s" ) &
done
wait

echo "== P9: subagent-style burst (4 agents x 3 sequential calls) =="
agent() {
  local id=$1
  for r in 1 2 3; do
    code=$(curl -s --max-time 30 -o /dev/null -w '%{http_code}' -H 'Content-Type: application/json' -H "Authorization: Bearer $FREEINFERENCE_API_KEY" -H "User-Agent: $UA_HONEST" -d '{"model":"glm-5.3-flash","messages":[{"role":"user","content":"reply with just: ok"}],"max_tokens":2}' $BASE/chat/completions)
    echo "agent$id/r$r: $code"
  done
}
for a in 1 2 3 4; do agent $a & done
wait

echo "== P10: 429 carries retry-after (headers of a saturated 3rd request) =="
( curl -s --max-time 25 -o /dev/null -H 'Content-Type: application/json' -H "Authorization: Bearer $FREEINFERENCE_API_KEY" -H "User-Agent: $UA_HONEST" -d '{"model":"glm-5.3-flash","messages":[{"role":"user","content":"count to 30 slowly"}],"max_tokens":100}' $BASE/chat/completions ) &
( curl -s --max-time 25 -o /dev/null -H 'Content-Type: application/json' -H "Authorization: Bearer $FREEINFERENCE_API_KEY" -H "User-Agent: $UA_HONEST" -d '{"model":"glm-5.3-flash","messages":[{"role":"user","content":"count to 30 slowly"}],"max_tokens":100}' $BASE/chat/completions ) &
sleep 0.3
curl -s --max-time 25 -D - -o /dev/null -H 'Content-Type: application/json' -H "Authorization: Bearer $FREEINFERENCE_API_KEY" -H "User-Agent: $UA_HONEST" -d '{"model":"glm-5.3-flash","messages":[{"role":"user","content":"hi"}],"max_tokens":2}' $BASE/chat/completions | grep -iE "^HTTP/|^retry-after|^x-request-id" 
wait

echo "== P11: pricing from GET /v1/models (USD/1M) =="
curl -s --max-time 10 -H "Authorization: Bearer $FREEINFERENCE_API_KEY" $BASE/models | python3 -c "
import json, sys
for m in json.load(sys.stdin)['data']:
    p = m.get('pricing') or {}
    print(f\"{m['id']:22s} in={p.get('prompt')} out={p.get('completion')} cacheR={p.get('input_cache_reads')} cacheW={p.get('input_cache_writes')} ctx={m.get('context_length')} out_len={m.get('max_output_length')}\")
"
