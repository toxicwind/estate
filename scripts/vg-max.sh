#!/usr/bin/env bash
# ============================================================================
# VG-MAX — All 148 models × GuideLLM sweep + Nuclei fuzz + PD cross-ref
# ============================================================================
set -uo pipefail
shopt -s expand_aliases lastpipe

RUN_ID="$(date +%Y-%m-%d_%H-%M-%S)"
ROOT="${MAX_ROOT:-$HOME/estate/log/vg-max}"
OUT="$ROOT/$RUN_ID"
mkdir -p "$OUT"/{bench,fuzz,artifacts,logs}
ln -sfn "$OUT" "$ROOT/latest"

KEY="${VERCEL_AI_GATEWAY_API_KEY:-${AI_GATEWAY_API_KEY:-}}"
BASE="https://ai-gateway.vercel.sh/v1"
UP="https://ai-gateway.vercel.sh/v1"
PDAUDIT="$(readlink -f $HOME/estate/log/pd-audit/latest)"

# Sweep parameters
MAX_SECONDS="${MAX_SECONDS:-30}"
PROMPT_TOKENS="${PROMPT_TOKENS:-256}"
OUTPUT_TOKENS="${OUTPUT_TOKENS:-128}"
STREAMS="${STREAMS:-1,4,16}"
PARALLEL_BENCH="${PARALLEL_BENCH:-4}"
FUZZ_TARGETS=148

MASTER="$OUT/logs/master.log"
exec > >(tee -a "$MASTER") 2>&1

R='\033[0;31m'; G='\033[0;32m'; Y='\033[0;33m'; B='\033[0;34m'
M='\033[0;35m'; C='\033[0;36m'; W='\033[1;37m'; D='\033[2m'; N='\033[0m'
TS() { date '+%H:%M:%S'; }
ok()   { printf "  ${G}✅${N} %s\n" "$*"; }
warn() { printf "  ${Y}⚠️${N}  %s\n" "$*"; }
err()  { printf "  ${R}❌${N} %s\n" "$*"; }
info() { printf "  ${C}ℹ️${N}  %s\n" "$*"; }
hdr()  { printf "\n${M}━━━ %s ━━━${N}\n" "$*"; }
sub()  { printf "\n${B}── %s ──${N}\n" "$*"; }

printf "${W}╔══════════════════════════════════════════════════════════════════════╗${N}\n"
printf "${W}║  VG-MAX — 148 models × GuideLLM sweep + Nuclei fuzz + PD cross-ref  ║${N}\n"
printf "${W}╚══════════════════════════════════════════════════════════════════════╝${N}\n"
info "run:      $RUN_ID"
info "out:      $OUT"
info "pd-audit: $PDAUDIT"
info "key:      ${KEY:0:10}… (len ${#KEY})"
echo ""

# ── §0 Preflight ────────────────────────────────────────────────────────────
hdr "0. Preflight"

[ -z "$KEY" ] && { err "no gateway key"; exit 1; }
ok "gateway key present"

for b in curl jq guidellm nuclei; do
  if command -v "$b" >/dev/null 2>&1; then
    ok "$b → $(command -v $b)"
  else
    err "$b missing"; exit 1
  fi
done

if [ ! -f "$PDAUDIT/artifacts/eligible.txt" ]; then
  err "pd-audit not found at $PDAUDIT"
  info "run: bash /home/toxic/estate/scripts/pd-audit.sh"
  exit 1
fi
ok "pd-audit found: $(wc -l < "$PDAUDIT/artifacts/eligible.txt") eligible models"

# Full model list — NO FILTER
cp "$PDAUDIT/artifacts/eligible.txt" "$OUT/artifacts/all-models.txt"
cp "$PDAUDIT/artifacts/osint.jsonl"   "$OUT/artifacts/osint.jsonl"
cp "$PDAUDIT/artifacts/eligibility.tsv" "$OUT/artifacts/eligibility.tsv"
N_MODELS=$(wc -l < "$OUT/artifacts/all-models.txt")
info "benchmarking ALL $N_MODELS models, no filter"
echo ""

# ── §1 Nuclei fuzz (background) ─────────────────────────────────────────────
hdr "1. Nuclei fuzzing harness (parallel)"

mkdir -p "$OUT/fuzz/templates"
cat > "$OUT/fuzz/templates/vg-model-fuzz.yaml" <<'YAML'
id: vg-model-fuzz
info:
  name: VG Model Fuzz
  author: estate
  severity: info
http:
  - pre-condition:
      - type: dsl
        dsl: ['method == "POST"', 'len(body) > 0']
        condition: and
    fuzzing:
      - part: body
        type: replace
        mode: single
        fuzz: ['{{model_id}}']
    matchers-condition: or
    matchers:
      - type: status
        status: [200,400,401,403,404,410,429,500,502,503]
    extractors:
      - type: json
        json: ['.error.type','.error.message','.choices[0].message.content']
YAML

# Build targets from all 148 models
jq -c -n --argjson M "$(jq -R -s 'split("\n")|map(select(.!=""))' < "$OUT/artifacts/all-models.txt")" '
  $M[] | {url:"https://ai-gateway.vercel.sh/v1/chat/completions",method:"POST",
    headers:{"Authorization":"Bearer '"$KEY"'","Content-Type":"application/json"},
    body:("{\"model\":\""+."\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],\"max_tokens\":4}")}
' > "$OUT/fuzz/targets.jsonl"
ok "wrote $(wc -l < "$OUT/fuzz/targets.jsonl") fuzz targets"

# Run nuclei fuzz in BACKGROUND
nuclei -fuzz -t "$OUT/fuzz/templates/" -l "$OUT/fuzz/targets.jsonl" \
  -jsonl -o "$OUT/fuzz/results.jsonl" \
  -c 64 -rl 400 -timeout 20 -retries 1 -silent -no-color \
  > "$OUT/logs/nuclei.log" 2>&1 &
NUCLEI_PID=$!
info "nuclei fuzz running in background (PID $NUCLEI_PID)"
echo ""

# ── §2 GuideLLM sweep — ALL models ──────────────────────────────────────────
hdr "2. GuideLLM sweep — ALL $N_MODELS models"

# Worker script
cat > "$OUT/bench/worker.sh" <<'BWORKER'
#!/usr/bin/env bash
M="$1"; K="$2"; BASE="$3"; OUT="$4"
MAX_S="$5"; PT="$6"; OT="$7"; ST="$8"
SLUG=$(echo "$M" | tr '/' '_' | tr -d ':')
BDIR="$OUT/$SLUG"
mkdir -p "$BDIR"
LOG="$BDIR/guidellm.log"

# Run guidellm with JSON+CSV+HTML
OPENAI_API_KEY="$K" guidellm run \
  --backend "kind=openai_http,target=$BASE,model=$M,api_key=$K" \
  --data "kind=synthetic_text,prompt_tokens=$PT,output_tokens=$OT" \
  --profile "kind=sweep" \
  --override "profile.streams" "$ST" \
  --constraint "kind=max_duration,seconds=$MAX_S" \
  --output "kind=json,path=$BDIR/bench.json" \
  --output "kind=csv,path=$BDIR/bench.csv" \
  --output "kind=html,path=$BDIR/bench.html" \
  --disable-console-interactive \
  > "$LOG" 2>&1

RC=$?
if [ $RC -eq 0 ] && [ -f "$BDIR/bench.json" ]; then
  echo "OK  $M  $BDIR/bench.json"
else
  echo "FAIL  $M  rc=$RC  $LOG"
fi
BWORKER
chmod +x "$OUT/bench/worker.sh"

sub "launching $N_MODELS benchmarks, $PARALLEL_BENCH parallel"
info "profile: sweep streams=$STREAMS  max_seconds=$MAX_SECONDS"
info "data:    prompt=$PROMPT_TOKENS  output=$OUTPUT_TOKENS"
echo ""

RESULT_LOG="$OUT/bench/results.tsv"
: > "$RESULT_LOG"

# Run all with parallelism, stream status as they complete
TS_BENCH_START=$(date +%s)
cat "$OUT/artifacts/all-models.txt" \
  | xargs -P "$PARALLEL_BENCH" -I {} "$OUT/bench/worker.sh" \
      {} "$KEY" "$BASE" "$OUT/bench" \
      "$MAX_SECONDS" "$PROMPT_TOKENS" "$OUTPUT_TOKENS" "$STREAMS" \
  | tee "$OUT/bench/status.log" \
  | while IFS= read -r line; do
      printf "  %s  %s\n" "$(TS)" "$line"
      echo "$line" >> "$RESULT_LOG"
    done
TS_BENCH_END=$(date +%s)
BENCH_DUR=$((TS_BENCH_END - TS_BENCH_START))
ok "benchmarks complete in ${BENCH_DUR}s"

N_OK=$(grep -c '^OK' "$RESULT_LOG" 2>/dev/null || echo 0)
N_FAIL=$(grep -c '^FAIL' "$RESULT_LOG" 2>/dev/null || echo 0)
info "succeeded: $N_OK  failed: $N_FAIL"
echo ""

# ── §3 Aggregate ────────────────────────────────────────────────────────────
hdr "3. Aggregate all benchmarks"

SUMMARY="$OUT/artifacts/summary.tsv"
printf 'model\trate\tstreams\ttpot_p50\tttft_p50\tttft_p99\titl_p50\tout_tps\treq_tps\terrors\n' > "$SUMMARY"

for D in "$OUT"/bench/*/; do
  J="$D/bench.json"
  [ ! -f "$J" ] && continue
  M=$(basename "$D" | tr '_' '/')
  jq -r --arg m "$M" '
    (.benchmarks // [])[]
    | [
        $m,
        (.rate // "-"), (.streams // "-"),
        (.metrics.time_to_first_token_ms.percentiles.p50 // "-"),
        (.metrics.time_to_first_token_ms.percentiles.p99 // "-"),
        (.metrics.time_per_output_token_ms.percentiles.p50 // "-"),
        (.metrics.inter_token_latency_ms.percentiles.p50 // "-"),
        (.metrics.output_tokens_per_second.mean // "-"),
        (.metrics.requests_per_second.mean // "-"),
        (.metrics.request_errors // 0)
      ] | @tsv
  ' "$J" 2>/dev/null >> "$SUMMARY"
done

N_ROWS=$(($(wc -l < "$SUMMARY") - 1))
ok "$N_ROWS metric rows in summary.tsv"
echo ""

sub "rank by output throughput (top 30)"
tail -n +2 "$SUMMARY" | sort -t$'\t' -k8 -rn | head -30 | \
  awk -F'\t' '{printf "  %-50s  out_tps=%-8s  ttft_p50=%-8s  streams=%s\n", $1, $8, $4, $3}'

echo ""
sub "models that errored"
tail -n +2 "$SUMMARY" | awk -F'\t' '$10 > 0 {printf "  %-50s  errors=%s\n", $1, $10}' | head -20
echo ""

# ── §4 Per-provider rollup ─────────────────────────────────────────────────
hdr "4. Per-provider aggregate"

jq -r 'select(.endpoints|length>0) | .endpoints[0].p + "\t" + .model' "$OUT/artifacts/osint.jsonl" 2>/dev/null \
  | sort -u > "$OUT/artifacts/model-provider.tsv"

{
  printf 'provider\tmodels\tavg_out_tps\tmax_out_tps\n'
  while IFS=$'\t' read -r P M; do
    SLUG=$(echo "$M" | tr '/' '_' | tr -d ':')
    J="$OUT/bench/$SLUG/bench.json"
    [ ! -f "$J" ] && continue
    jq -r --arg p "$P" '
      (.benchmarks // [])[]
      | "\($p)\t\(.metrics.output_tokens_per_second.mean // 0)"
    ' "$J" 2>/dev/null
  done < "$OUT/artifacts/model-provider.tsv"
} | awk -F'\t' 'NR>1 {c[$1]++; s[$1]+=$2; if($2>m[$1])m[$1]=$2} END {for(p in c) printf "%s\t%d\t%.2f\t%.2f\n", p, c[p], s[p]/c[p], m[p]}' \
  | sort -t$'\t' -k4 -rn | column -t -s$'\t' | head -30

# ── §5 Wait for nuclei ─────────────────────────────────────────────────────
hdr "5. Nuclei fuzz results"

wait "$NUCLEI_PID" 2>/dev/null || true
if [ -f "$OUT/fuzz/results.jsonl" ]; then
  N_FUZZ=$(wc -l < "$OUT/fuzz/results.jsonl")
  ok "$N_FUZZ fuzz findings"
  sub "by status"
  jq -r '.info.severity // "?"' "$OUT/fuzz/results.jsonl" 2>/dev/null | sort | uniq -c | sed 's/^/    /'
  sub "sample findings"
  jq -r '"  \(.host)  [\(.template_id)]"' "$OUT/fuzz/results.jsonl" 2>/dev/null | head -20
else
  warn "no fuzz results — check $OUT/logs/nuclei.log"
fi
echo ""

# ── §6 Export reports ──────────────────────────────────────────────────────
hdr "6. Report exports"

sub "re-exports (HTML)"
for D in "$OUT"/bench/*/; do
  J="$D/bench.json"
  [ ! -f "$J" ] && continue
  guidellm export "$J" --output "kind=html,path=$D/report.html" 2>/dev/null || true
done
N_HTML=$(find "$OUT/bench" -name 'report.html' 2>/dev/null | wc -l)
ok "$N_HTML html reports"

sub "combined CSV"
cp "$SUMMARY" "$OUT/artifacts/summary.csv"

sub "manifest"
{
  echo "RUN_ID=$RUN_ID"
  echo "MODELS=$N_MODELS"
  echo "OK=$N_OK"
  echo "FAIL=$N_FAIL"
  echo "BENCH_SECONDS=$BENCH_DUR"
  echo "NUCLEI_FINDINGS=$N_FUZZ"
  echo "GATEWAY=$BASE"
  echo "SWEEP_STREAMS=$STREAMS"
} > "$OUT/artifacts/manifest.env"
cat "$OUT/artifacts/manifest.env" | sed 's/^/  /'

# ── §7 Final ───────────────────────────────────────────────────────────────
hdr "7. FINAL"

SIZE=$(du -sh "$OUT" 2>/dev/null | awk '{print $1}')
info "run:      $RUN_ID"
info "out:      $OUT"
info "size:     $SIZE"
info "models:   $N_OK/$N_MODELS benchmarked"
info "fuzz:     $N_FUZZ findings"
echo ""

sub "top 5 models by output tps"
tail -n +2 "$SUMMARY" | sort -t$'\t' -k8 -rn | head -5 | \
  awk -F'\t' '{printf "  %-50s  %s t/s\n", $1, $8}'

sub "top 5 by latency (lowest ttft_p50)"
tail -n +2 "$SUMMARY" | awk -F'\t' '$4!="-"' | sort -t$'\t' -k4 -n | head -5 | \
  awk -F'\t' '{printf "  %-50s  ttft_p50=%sms  %s t/s\n", $1, $4, $8}'

echo ""
sub "artifacts"
find "$OUT" -maxdepth 2 -type f \( -name '*.json' -o -name '*.tsv' -o -name '*.csv' -o -name '*.html' -o -name '*.env' \) \
  -size +1k 2>/dev/null | head -40 | while read f; do
    printf "  %-70s  %s\n" "${f#$OUT/}" "$(du -h "$f" | cut -f1)"
  done

echo ""
printf "${W}════════════════════════════════════════════════════════════════════${N}\n"
printf "${W} DONE — results in ${C}$OUT${W}${N}\n"
printf "${W}════════════════════════════════════════════════════════════════════${N}\n"
echo ""
printf "  ${C}cat %s/artifacts/summary.tsv | column -t${N}\n" "$OUT"
printf "  ${C}find %s/bench -name report.html${N}\n" "$OUT"
printf "  ${C}jq '.benchmarks[0].metrics' %s/bench/*/bench.json | head -50${N}\n" "$OUT"
echo ""
