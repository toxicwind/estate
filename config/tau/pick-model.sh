#!/usr/bin/env bash
# pick-model.sh — pure-completions ranking. No metadata trust.
# Every discovered model is probed with identical deterministic questions.
# Ranking = number of exact-match answers. Fail-fast on first 4/4.
set -uo pipefail

LOG=/tmp/pick-model.log
RAW=/tmp/models-raw.json
WIN=/tmp/best_model.txt
LOCK=/tmp/pick.lock
CONCURRENCY="${PICK_CONCURRENCY:-8}"

: > "$LOG"; rm -f "$WIN"; rm -rf "$LOCK"

ENDPOINT='http://127.0.0.1:25193'
KEY="${FLOCK_API_KEY:-}"; [[ -z "$KEY" && -f ~/.tau/flock.key ]] && KEY=$(<~/.tau/flock.key)
[[ -z "$KEY" ]] && { echo "NO FLOCK KEY" >&2; exit 3; }

# Only exclude non-flock aliases. Everything else gets a fair shot.
BLACKLIST='^local/|^herd/'

# ---------- discovery: pure ID list, no health filter ----------
discover() {
  curl -s -m 10 -H "Authorization: Bearer $KEY" "$ENDPOINT/v1/models" > "$RAW" 2>/dev/null || true
  jq -r '.data[]?.id // empty' "$RAW" 2>/dev/null \
    | grep -Ev "$BLACKLIST" \
    | sort -u
}

# ---------- one deterministic probe ----------
ask() {
  jq -nc --arg m "$1" --arg c "$2" \
    '{model:$m,messages:[{role:"user",content:$c}],max_tokens:8,temperature:0}' \
  | curl -s -m 30 -X POST "$ENDPOINT/v1/chat/completions" \
      -H "Authorization: Bearer $KEY" \
      -H 'Content-Type: application/json' -d @- \
  | jq -r '.choices[0].message.content // ""' 2>/dev/null
}
norm() { tr -d '[:space:]' <<<"${1,,}" | head -c 32; }

# ---------- score one model: 4 exact-match probes, fail-fast per step ----------
score_one() {
  local m=$1 s=0 a b c d
  [[ -e "$LOCK" ]] && return 0

  a=$(ask "$m" '17*23? number only')
  [[ -e "$LOCK" ]] && return 0
  b=$(ask "$m" 'A=>B, B=>C, A true. C? yes/no')
  [[ -e "$LOCK" ]] && return 0
  c=$(ask "$m" 'r count in strawberry? number only')
  [[ -e "$LOCK" ]] && return 0
  d=$(ask "$m" 'JSON only: {"ok":true,"n":42}')
  [[ -e "$LOCK" ]] && return 0

  [[ "$(norm "$a")" == "391" ]]                && ((s+=1))
  [[ "$(norm "$b")" == "yes" ]]                && ((s+=1))
  [[ "$(norm "$c")" == "3"   ]]                && ((s+=1))
  [[ "$(norm "$d")" == '{"ok":true,"n":42}' ]] && ((s+=1))

  # single append per model — atomic under 4KB on POSIX
  printf '%s|%s|a=%s|b=%s|c=%s|d=%s\n' \
    "$s" "$m" "$(norm "$a")" "$(norm "$b")" "$(norm "$c")" "$(norm "$d")" >> "$LOG"

  if (( s >= 4 )) && mkdir "$LOCK" 2>/dev/null; then
    echo "$m" > "$WIN"
    echo "WIN $m (4/4)" >&2
  fi
}

# ---------- run ----------
mapfile -t MODELS < <(discover)
if (( ${#MODELS[@]} == 0 )); then
  echo "NO MODELS DISCOVERED — $RAW" >&2
  head -c 400 "$RAW" >&2; echo >&2
  exit 1
fi
echo "PROBING ${#MODELS[@]} models, concurrency=$CONCURRENCY, pure completions" >&2

for m in "${MODELS[@]}"; do
  [[ -e "$LOCK" ]] && break
  # bound concurrency: wait until a slot frees
  while (( $(jobs -rp | wc -l) >= CONCURRENCY )); do
    [[ -e "$LOCK" ]] && break
    sleep 0.1
  done
  score_one "$m" &
done

# supervisor: kill everyone the moment a 4/4 lands
while :; do
  if [[ -e "$LOCK" ]]; then
    sleep 0.2
    kill $(jobs -p) 2>/dev/null
    break
  fi
  jobs -p | grep -q . || break
  sleep 0.3
done
wait 2>/dev/null

# ---------- resolve ----------
if [[ -f "$WIN" ]]; then
  cat "$WIN"; exit 0
fi

# nobody 4/4 — rank by score, use top if >= 2
best=$(sort -t'|' -k1,1nr -k2,2 "$LOG" | head -1)
IFS='|' read -r bs bm _ <<<"$best"
if [[ -n "$bm" && "$bs" -ge 2 ]]; then
  echo "WARN: nobody 4/4 — best $bm ($bs/4)" >&2
  echo "$bm" > "$WIN"; cat "$WIN"; exit 0
fi

echo "NOTHING >=2/4:" >&2
sort -t'|' -k1,1nr "$LOG" | head -20 >&2
exit 1
