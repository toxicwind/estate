#!/usr/bin/env bash
# ============================================================================
# VG-BENCH — GuideLLM sweep benchmark against Vercel AI Gateway free lanes
# ============================================================================
# Install: pip install guidellm
# Target:  https://ai-gateway.vercel.sh/v1 (OpenAI-compatible)
# Models:  the 5 free lanes discovered by pd-audit
# Output:  JSON + CSV per model + combined report
# ============================================================================

set -uo pipefail

RUN_ID="$(date +%Y-%m-%d_%H-%M-%S)"
ROOT="${BENCH_ROOT:-$HOME/estate/log/vg-bench}"
OUT="$ROOT/$RUN_ID"
mkdir -p "$OUT"
ln -sfn "$OUT" "$ROOT/latest"

KEY="${VERCEL_AI_GATEWAY_API_KEY:-${AI_GATEWAY_API_KEY:-}}"
BASE="https://ai-gateway.vercel.sh/v1"

# Models from the pd-audit §5 free-lane extraction
MODELS=(
  "poolside/laguna-s-2.1-free"
  "inclusionai/ling-3.1-flash"
  "inclusionai/ling-3.0-flash-sante"
  "inclusionai/ling-3.1-flash-free"
  "inclusionai/ling-3.0-flash-sante-free"
)

# Sweep parameters — "hard test"
MAX_SECONDS="${MAX_SECONDS:-45}"
PROMPT_TOKENS="${PROMPT_TOKENS:-512}"
OUTPUT_TOKENS="${OUTPUT_TOKENS:-256}"
OVERRIDE_STREAMS="${OVERRIDE_STREAMS:-1,2,4,8,16,32}"

exec > >(tee -a "$OUT/master.log") 2>&1

R='\033[0;31m'; G='\033[0;32m'; Y='\033[0;33m'; C='\033[0;36m'; M='\033[0;35m'; N='\033[0m'
ok()   { printf "  ${G}✅${N} %s\n" "$*"; }
warn() { printf "  ${Y}⚠️${N}  %s\n" "$*"; }
err()  { printf "  ${R}❌${N} %s\n" "$*"; }
info() { printf "  ${C}ℹ️${N}  %s\n" "$*"; }
hdr()  { printf "\n${M}━━━ %s ━━━${N}\n" "$*"; }

# ── 0. Preflight ────────────────────────────────────────────────────────────
hdr "0. Preflight"
info "run:   $RUN_ID"
info "out:   $OUT"
info "key:   ${KEY:0:10}… (len ${#KEY})"
info "target: $BASE"

if [ -z "$KEY" ]; then
  err "VERCEL_AI_GATEWAY_API_KEY / AI_GATEWAY_API_KEY unset"
  exit 1
fi

if ! command -v guidellm >/dev/null 2>&1; then
  warn "guidellm not found — installing"
  if command -v pipx >/dev/null 2>&1; then
    pipx install guidellm 2>&1 | tail -5
  else
    pip install --user "guidellm[recommended]" 2>&1 | tail -5
  fi
  hash -r
fi

if ! command -v guidellm >/dev/null 2>&1; then
  err "guidellm install failed"
  exit 1
fi
ok "guidellm: $(guidellm --version 2>&1 | head -1)"

# ── 1. Sanity: gateway reachable + key valid ────────────────────────────────
hdr "1. Gateway sanity"
for M in "${MODELS[@]}"; do
  printf '  %-45s ' "$M"
  C=$(curl -s -o /dev/null -w "%{http_code}" --max-time 20 \
    "$BASE/chat/completions" \
    -H "Authorization: Bearer $KEY" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"$M\",\"messages\":[{\"role\":\"user\",\"content\":\"ok\"}],\"max_tokens\":2}")
  case "$C" in
    200) printf "${G}%s${N}\n" "$C" ;;
    429) printf "${Y}%s (rate-limited)${N}\n" "$C" ;;
    *)   printf "${R}%s${N}\n" "$C" ;;
  esac
done

# ── 2. Benchmark each model ─────────────────────────────────────────────────
hdr "2. Sweep benchmarks"
info "profile:        sweep (auto-discovers max tput)"
info "streams sweep:  $OVERRIDE_STREAMS"
info "prompt tokens:  $PROMPT_TOKENS"
info "output tokens:  $OUTPUT_TOKENS"
info "max seconds:    $MAX_SECONDS per strategy"
echo ""

declare -A RESULTS
for M in "${MODELS[@]}"; do
  SLUG=$(echo "$M" | tr '/' '_' | tr -d ':')
  JSON="$OUT/${SLUG}.json"
  CSV="$OUT/${SLUG}.csv"

  hdr "▸ $M"

  # GuideLLM run with OpenAI-compatible backend
  # API key passed via OPENAI_API_KEY env (guidellm reads it for openai_http)
  OPENAI_API_KEY="$KEY" guidellm run \
    --backend "kind=openai_http,target=$BASE,model=$M" \
    --data "kind=synthetic_text,prompt_tokens=$PROMPT_TOKENS,output_tokens=$OUTPUT_TOKENS" \
    --profile "kind=sweep" \
    --override "profile.streams" "$OVERRIDE_STREAMS" \
    --constraint "kind=max_duration,seconds=$MAX_SECONDS" \
    --output-dir "$OUT" \
    --outputs "json,csv" \
    2>&1 | tee "$OUT/${SLUG}.log" | tail -40

  # GuideLLM writes a generic name; rename to per-model
  if [ -f "$OUT/benchmarks.json" ]; then
    mv "$OUT/benchmarks.json" "$JSON"
  fi
  if [ -f "$OUT/benchmarks.csv" ]; then
    mv "$OUT/benchmarks.csv" "$CSV"
  fi

  if [ -f "$JSON" ]; then
    ok "results → $JSON"
    RESULTS[$M]="$JSON"
  else
    warn "no JSON output for $M"
  fi
  echo ""
done

# ── 3. Aggregate ────────────────────────────────────────────────────────────
hdr "3. Aggregate results"

SUMMARY="$OUT/summary.tsv"
printf 'model\trate\tstreams\tttft_p50_ms\tttft_p99_ms\ttpot_p50_ms\titl_p50_ms\toutput_tps\trequest_tps\n' > "$SUMMARY"

for M in "${MODELS[@]}"; do
  J="${RESULTS[$M]:-}"
  [ -z "$J" ] || [ ! -f "$J" ] && continue
  jq -r --arg m "$M" '
    (.benchmarks // [])[]
    | . as $b
    | ($b.metrics // {}) as $mt
    | [
        $m,
        ($b.rate // "-"),
        ($b.streams // "-"),
        ($mt.ttft_ms.p50 // "-"),
        ($mt.ttft_ms.p99 // "-"),
        ($mt.tpot_ms.p50 // "-"),
        ($mt.itl_ms.p50 // "-"),
        ($mt.output_tokens_per_second.mean // "-"),
        ($mt.requests_per_second.mean // "-")
      ] | @tsv
  ' "$J" >> "$SUMMARY" 2>/dev/null
done

column -t -s$'\t' "$SUMMARY" | tee "$OUT/summary.txt"

# ── 4. Rank by throughput ───────────────────────────────────────────────────
hdr "4. Rank by max output throughput (t/s)"

tail -n +2 "$SUMMARY" | sort -t$'\t' -k8 -rn | head -20 | \
  awk -F'\t' '{printf "  %-45s  tps=%s  ttft_p50=%sms  streams=%s\n", $1, $8, $4, $3}'

# ── 5. Best model per SLO target ────────────────────────────────────────────
hdr "5. Best model per SLO (ttft_p50 < 1000ms)"

tail -n +2 "$SUMMARY" | awk -F'\t' '$4 != "-" && $4 < 1000' | \
  sort -t$'\t' -k8 -rn | head -10 | \
  awk -F'\t' '{printf "  %-45s  tps=%s  ttft_p50=%sms\n", $1, $8, $4}'

# ── 6. Summary block ────────────────────────────────────────────────────────
hdr "6. FINAL"
echo ""
info "run dir:  $OUT"
info "summary:  $SUMMARY"
info "results:"
for M in "${MODELS[@]}"; do
  SLUG=$(echo "$M" | tr '/' '_' | tr -d ':')
  [ -f "$OUT/${SLUG}.json" ] && printf "    %-45s %s\n" "$M" "$OUT/${SLUG}.json"
done
echo ""
info "re-export any result:"
info "  guidellm benchmark from-file $OUT/<model>.json --outputs html --output-dir $OUT"
echo ""
printf "${M}════════════════════════════════════════════════════════════════${N}\n"

