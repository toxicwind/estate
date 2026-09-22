#!/usr/bin/env bash
# verify-modelmap.sh -- post-fix verification for the 2026-09-21 modelmap push.
# Runs ON YOTE (herd :25100, shims :2515x, sovereign-router :25104 are loopback).
# Usage: ./verify-modelmap.sh
# Exit 0 = all routes honest (live or honest-upstream-error). Exit 1 = broken routing found.
set -u
HERD="http://127.0.0.1:25100"
PASS=0; HONEST=0; BROKEN=0
declare -a BROKEN_LIST

# probe <base> <model> -- POST a tiny completion, classify the result.
probe() {
  local base="$1" model="$2"
  local start end ms code body err
  start=$(date +%s%3N)
  body=$(curl -s -m 60 -w '\n%{http_code}' -X POST "$base/v1/chat/completions" \
    -H 'Content-Type: application/json' \
    -d "{\"model\":\"$model\",\"messages\":[{\"role\":\"user\",\"content\":\"Reply with the single word PONG.\"}],\"max_tokens\":16}" 2>/dev/null)
  end=$(date +%s%3N); ms=$((end-start))
  code=$(printf '%s' "$body" | tail -1)
  body=$(printf '%s' "$body" | head -n -1)
  local content
  content=$(printf '%s' "$body" | python3 -c "
import json,sys
try:
  d=json.load(sys.stdin)
  ch=d.get('choices',[{}])[0].get('message',{}).get('content','')
  print('SUBSTANCE' if ch and ch.strip() else 'EMPTY')
except Exception as e:
  print('ERR:'+str(e)[:60])
" 2>/dev/null)
  if [[ "$code" == "200" && "$content" == "SUBSTANCE" ]]; then
    echo "PASS   ${ms}ms  $model  -> live completion"
    PASS=$((PASS+1))
  elif [[ "$code" == "429" || "$code" == "402" ]]; then
    echo "HONEST ${ms}ms  $model  -> HTTP $code (upstream billing/quota, routing OK)"
    HONEST=$((HONEST+1))
  else
    echo "BROKEN ${ms}ms  $model  -> HTTP $code content=$content"
    BROKEN=$((BROKEN+1)); BROKEN_LIST+=("$model (HTTP $code)")
  fi
}

echo "=== herd :25100 alias probes (2026-09-21 modelmap) ==="
for m in kimi kimi-k2 kimi-code kimi-auto \
         oracle-judge-a oracle-judge-b oracle-judge-c oracle-judge-local \
         fast tiny small medium code long qwen-flash-da-128k; do
  probe "$HERD" "$m"
done
echo "=== herd :25100 direct peer-ID probes ==="
for m in "nex-agi/nex-n2.5-pro:free" "gemini-3-flash-preview" "kimi-k2.6" "ministral-14b-latest"; do
  probe "$HERD" "$m"
done
echo "=== pitchfork kimi-auto-shim :25153 ==="
probe "http://127.0.0.1:25153" "kimi-auto"
echo "=== sovereign-router :25104 (tau 'sovereign' provider) ==="
probe "http://127.0.0.1:25104" "free"

echo
echo "=== summary: PASS=$PASS HONEST(429/402)=$HONEST BROKEN=$BROKEN ==="
if (( BROKEN > 0 )); then
  printf 'BROKEN: %s\n' "${BROKEN_LIST[@]}"
  exit 1
fi
echo "Model map is clean: every route is live or fails honestly upstream."
