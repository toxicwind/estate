#!/usr/bin/env bash
# smoke.sh — live smoke test for the tau-flock extension's flock client.
#
# Hits the LIVE flock daemon at 127.0.0.1:8000 and asserts:
#   1. GET /health            -> "ok"
#   2. GET /v1/models         -> non-empty data list  (needs proxy API key)
#   3. POST /v1/chat/completions -> NON-EMPTY message content (needs proxy API key)
#
# Key resolution (never printed, only reported present/absent):
#   FLOCK_API_KEY -> NVIDIA_API_KEY -> NIM_PROXY_API_KEY (env only).
# If no key is present in env, the script reports exactly that and degrades
# to proving /health (+ /v1/models if the proxy answers without a key).
#
# Fail-loud: any failed assertion exits non-zero with a diagnostic.
set -euo pipefail

BASE="${FLOCK_BASE_URL:-http://127.0.0.1:8000}"
BASE="${BASE%/}"
CHAT_PROMPT="${FLOCK_SMOKE_PROMPT:-Reply with exactly: smoke-test-ok}"

KEY_SOURCE=""
KEY=""
for var in FLOCK_API_KEY NVIDIA_API_KEY NIM_PROXY_API_KEY; do
  if [ -n "${!var:-}" ]; then
    KEY="${!var}"
    KEY_SOURCE="$var"
    break
  fi
done

fail() { echo "SMOKE FAIL: $*" >&2; exit 1; }
pass() { echo "SMOKE PASS: $*"; }

echo "== flock smoke test =="
echo "base: $BASE"
if [ -n "$KEY" ]; then
  echo "proxy API key: present (via $KEY_SOURCE) — value NOT shown"
else
  echo "proxy API key: ABSENT from env (checked FLOCK_API_KEY, NVIDIA_API_KEY, NIM_PROXY_API_KEY)"
  # Check well-known key store locations for presence only — never print values.
  for store in /home/toxic/.secrets; do
    if [ -d "$store" ]; then
      if grep -lq -E 'NVIDIA_API_KEY|NIM_PROXY_API_KEY' "$store"/* 2>/dev/null; then
        echo "key-store check: $store contains a NVIDIA_API_KEY/NIM_PROXY_API_KEY entry (presence only)"
      else
        echo "key-store check: $store present, no NVIDIA_API_KEY/NIM_PROXY_API_KEY entry found"
      fi
    else
      echo "key-store check: $store not present"
    fi
  done
fi
echo

# ---- 1. /health ------------------------------------------------------------
echo "-- GET /health"
t0=$(date +%s%3N 2>/dev/null || date +%s)
HEALTH_BODY="$(curl -sS --max-time 10 -w '\n%{http_code}' "$BASE/health")" || fail "curl /health failed"
HEALTH_CODE="$(printf '%s' "$HEALTH_BODY" | tail -n 1)"
HEALTH_TEXT="$(printf '%s' "$HEALTH_BODY" | head -n -1)"
t1=$(date +%s%3N 2>/dev/null || date +%s)
[ "$HEALTH_CODE" = "200" ] || fail "/health HTTP $HEALTH_CODE body: $HEALTH_TEXT"
[ "$HEALTH_TEXT" = "ok" ] || fail "/health body was '$HEALTH_TEXT', expected 'ok'"
pass "/health -> ok"
echo "   measured: $((t1 - t0)) ms"
echo

# ---- auth-gated section ----------------------------------------------------
if [ -z "$KEY" ]; then
  echo "-- /v1/models (no key in env; reporting raw result)"
  RAW="$(curl -sS --max-time 15 -w '\n%{http_code}' "$BASE/v1/models")" || fail "curl /v1/models failed"
  CODE="$(printf '%s' "$RAW" | tail -n 1)"
  echo "   HTTP $CODE"
  if [ "$CODE" = "401" ] || [ "$CODE" = "403" ]; then
    echo "   NOTE: /v1/models requires a proxy API key and none is present in env."
    echo "   Chat completions are untestable without it. Degraded to /health proof."
  fi
  echo
  echo "RESULT: DEGRADED — /health proven. /v1/models and /v1/chat/completions require FLOCK_API_KEY (absent)."
  exit 2
fi

auth_header() { echo "Authorization: Bearer $KEY"; }

# ---- 2. /v1/models ----------------------------------------------------------
echo "-- GET /v1/models (key via $KEY_SOURCE)"
t0=$(date +%s%3N 2>/dev/null || date +%s)
MODELS_JSON="$(curl -sS --max-time 20 -H "$(auth_header)" "$BASE/v1/models")" \
  || fail "curl /v1/models failed"
t1=$(date +%s%3N 2>/dev/null || date +%s)
MODEL_COUNT="$(printf '%s' "$MODELS_JSON" | python3 -c 'import sys,json; print(len(json.load(sys.stdin)["data"]))')" \
  || fail "/v1/models did not return a data list: $(printf '%s' "$MODELS_JSON" | head -c 300)"
[ "$MODEL_COUNT" -gt 0 ] || fail "/v1/models returned an empty list"
MODEL_ID="$(printf '%s' "$MODELS_JSON" | python3 -c 'import sys,json; print(json.load(sys.stdin)["data"][0]["id"])')"
pass "/v1/models -> $MODEL_COUNT models ($((t1 - t0)) ms); first: $MODEL_ID"
echo

# ---- 3. /v1/chat/completions ------------------------------------------------
echo "-- POST /v1/chat/completions (model: $MODEL_ID)"
PAYLOAD="$(python3 -c 'import json,sys; print(json.dumps({"model": sys.argv[1], "messages": [{"role": "user", "content": sys.argv[2]}]}))' "$MODEL_ID" "$CHAT_PROMPT")"
t0=$(date +%s%3N 2>/dev/null || date +%s)
CHAT_JSON="$(curl -sS --max-time 90 -H "$(auth_header)" -H 'Content-Type: application/json' \
  -d "$PAYLOAD" "$BASE/v1/chat/completions")" || fail "curl /v1/chat/completions failed"
t1=$(date +%s%3N 2>/dev/null || date +%s)
CHAT_MODEL="$(printf '%s' "$CHAT_JSON" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("model",""))' 2>/dev/null || true)"
CONTENT="$(printf '%s' "$CHAT_JSON" | python3 -c '
import sys,json
d = json.load(sys.stdin)
ch = (d.get("choices") or [{}])[0]
msg = (ch.get("message") or {}).get("content")
print(msg if isinstance(msg, str) else "")
' 2>/dev/null || true)"
[ -n "$CONTENT" ] || fail "/v1/chat/completions returned EMPTY content (model=${CHAT_MODEL:-?}). Raw head: $(printf '%s' "$CHAT_JSON" | head -c 300)"
[ -n "${CONTENT//[[:space:]]/}" ] || fail "/v1/chat/completions returned whitespace-only content"
pass "/v1/chat/completions -> non-empty ($((t1 - t0)) ms)"
echo "   model id: ${CHAT_MODEL:-$MODEL_ID}"
echo "   content (first 200 chars): ${CONTENT:0:200}"
echo
echo "RESULT: OK — /health, /v1/models ($MODEL_COUNT models), and /v1/chat/completions all proven live."
