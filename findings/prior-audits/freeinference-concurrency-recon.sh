#!/usr/bin/env bash
# freeinference-concurrency-recon.sh — ferret-methodology probe matrix
# Question: does freeinference enforce "Too many concurrent requests (limit: 1)"?
# Lanes: (1) same model x2 concurrent, (2) two different models concurrent,
#        (3) different User-Agents concurrent, (4) OpenAI shape vs Claude shape.
# Results: /tmp/kilo/freeinf-recon.jsonl  + stdout PASS/FAIL verdicts.
set -uo pipefail
K=$(grep -E '^FREEINFERENCE_API_KEY=' /home/toxic/.secrets | cut -d= -f2-)
BASE=https://freeinference.org/v1
OUT=/tmp/kilo/freeinf-recon.jsonl
: > "$OUT"

probe() { # probe <tag> <json-body> <ua> <endpoint>
  local tag="$1" body="$2" ua="$3" ep="${4:-/chat/completions}"
  local t0 rc resp
  t0=$(date +%s.%N)
  resp=$(curl -s -m 30 -w '\n%{http_code}' -X POST "$BASE$ep" \
    -H "Authorization: Bearer $K" -H 'Content-Type: application/json' \
    -H "User-Agent: $ua" -d "$body" 2>&1)
  rc=$?
  local t1 code
  t1=$(date +%s.%N); code=$(echo "$resp" | tail -1)
  printf '{"tag":"%s","ua":"%s","ep":"%s","rc":%s,"http":%s,"ms":%.0f,"body":%s}\n' \
    "$tag" "$ua" "$ep" "$rc" "$code" \
    "$(echo "$t0 $t1" | awk '{printf "%.0f", ($2-$1)*1000}')" \
    "$(echo "$resp" | head -n -1 | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()[:220]))' 2>/dev/null || echo '""')" >> "$OUT"
  echo "$tag: http=$code ms=$(echo "$t0 $t1" | awk '{printf "%.0f", ($2-$1)*1000}')"
}

OPEN_BODY='{"model":"glm-5.3-flash","messages":[{"role":"user","content":"reply with exactly: OK"}],"max_tokens":8}'
DS_BODY='{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"reply with exactly: OK"}],"max_tokens":8}'

echo "=== lane 1: SAME model x2 concurrent ==="
probe "same-a" "$OPEN_BODY" "curl/8.9" &
probe "same-b" "$OPEN_BODY" "curl/8.9" &
wait

echo "=== lane 2: two DIFFERENT models concurrent ==="
probe "diff-glm" "$OPEN_BODY" "curl/8.9" &
probe "diff-ds" "$DS_BODY" "curl/8.9" &
wait

echo "=== lane 3: different user-agents concurrent ==="
probe "ua-openai" "$OPEN_BODY" "OpenAI/Python 1.54.0" &
probe "ua-tau" "$OPEN_BODY" "tau/18.8.4-estate.tau" &
probe "ua-claude-cli" "$OPEN_BODY" "claude-cli/2.0.0 (external, cli)" &
wait

echo "=== lane 4: claude shape (/v1/messages) vs openai shape concurrent ==="
CLAUDE_BODY='{"model":"glm-5.3-flash","max_tokens":8,"messages":[{"role":"user","content":"reply with exactly: OK"}]}'
probe "shape-anthropic" "$CLAUDE_BODY" "anthropic-sdk-python/0.39.0" "/messages" &
probe "shape-openai" "$OPEN_BODY" "OpenAI/Python 1.54.0" "/chat/completions" &
wait

echo "=== verdicts ==="
python3 - "$OUT" <<'PYEOF'
import json, sys, collections
rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
for r in rows:
    verdict = "PASS" if r["http"] == 200 else ("RATE-LIMITED" if "concurrent" in (r["body"] or "") else "FAIL")
    print(f'{verdict:13} {r["tag"]:18} http={r["http"]} {r["ms"]}ms  {(r["body"] or "")[:110]}')
limited = [r for r in rows if "concurrent" in (r["body"] or "")]
print(f"\nrate-limited lanes: {len(limited)} / {len(rows)}")
PYEOF
