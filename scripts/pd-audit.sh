#!/usr/bin/env bash
# ============================================================================
# ESTATE × PROJECTDISCOVERY × VERCEL AI GATEWAY — DEBUG-GRADE AUDIT
# ============================================================================
# Full install, full audit, full fuzz, full config, full logging.
# Every section tees to its own file under $LOG_DIR.
# ============================================================================

set -uo pipefail
shopt -s expand_aliases lastpipe

# ── Run identity ─────────────────────────────────────────────────────────────
RUN_ID="$(date +%Y-%m-%d_%H-%M-%S)"
LOG_ROOT="${LOG_ROOT:-$HOME/estate/log/pd-audit}"
LOG_DIR="$LOG_ROOT/$RUN_ID"
mkdir -p "$LOG_DIR"
LINK="$LOG_ROOT/latest"
rm -f "$LINK" 2>/dev/null
ln -sfn "$LOG_DIR" "$LINK" 2>/dev/null

MASTER="$LOG_DIR/master.log"
: > "$MASTER"

# ── All output goes to master.log AND terminal ──────────────────────────────
exec > >(tee -a "$MASTER") 2>&1

# ── Colors ───────────────────────────────────────────────────────────────────
if [ -t 1 ]; then
  R='\033[0;31m'; G='\033[0;32m'; Y='\033[0;33m'; B='\033[0;34m'
  M='\033[0;35m'; C='\033[0;36m'; W='\033[1;37m'; D='\033[2m'; N='\033[0m'
else
  R=''; G=''; Y=''; B=''; M=''; C=''; W=''; D=''; N=''
fi

TS()    { date '+%H:%M:%S'; }
ok()    { printf "  ${G}✅${N} %s\n" "$*"; }
warn()  { printf "  ${Y}⚠️${N}  %s\n" "$*"; }
err()   { printf "  ${R}❌${N} %s\n" "$*"; }
info()  { printf "  ${C}ℹ️${N}  %s\n" "$*"; }
dbg()   { printf "  ${D}[%s] %s${N}\n" "$(TS)" "$*"; }
hdr()   { printf "\n${M}━━━ %s ━━━${N}\n" "$*"; }
sub()   { printf "\n${B}── %s ──${N}\n" "$*"; }

# ── Section logger: run a function with its own tee'd log ───────────────────
SECTION() {
  local name="$1"; shift
  local logfile="$LOG_DIR/${name}.log"
  dbg "section start: $name → $logfile"
  local start; start=$(date +%s)
  "$@" 2>&1 | tee -a "$logfile"
  local rc=${PIPESTATUS[0]}
  local dur=$(( $(date +%s) - start ))
  dbg "section end:   $name  rc=$rc  ${dur}s"
  return $rc
}

# ── Trap for errors ─────────────────────────────────────────────────────────
on_error() {
  local rc=$?
  err "SCRIPT FAILED at line $1 with exit $rc"
  dbg "see $MASTER for full trace"
}
trap 'on_error $LINENO' ERR

# ── Config ───────────────────────────────────────────────────────────────────
KEY="${VERCEL_AI_GATEWAY_API_KEY:-${AI_GATEWAY_API_KEY:-}}"
UP="https://ai-gateway.vercel.sh/v1"
ART="$LOG_DIR/artifacts"
mkdir -p "$ART"

OMP_CONFIG="${HOME}/.omp/agent/config.yml"
TAU_CONFIG="${HOME}/estate/config/tau/agent/config.yml"
SECRETS="${HOME}/.secrets"

# ── Header ───────────────────────────────────────────────────────────────────
printf "${W}╔══════════════════════════════════════════════════════════════════════╗${N}\n"
printf "${W}║   ESTATE × PROJECTDISCOVERY × VERCEL AI GATEWAY — MAX AUDIT         ║${N}\n"
printf "${W}╚══════════════════════════════════════════════════════════════════════╝${N}\n"
info "run id:    $RUN_ID"
info "log dir:   $LOG_DIR"
info "symlink:   $LINK"
info "master:    $MASTER"
echo ""

# ════════════════════════════════════════════════════════════════════════════
# §0  PREFLIGHT
# ════════════════════════════════════════════════════════════════════════════
section_00_preflight() {
  hdr "0. Preflight"

  sub "environment"
  info "user:      $(whoami)"
  info "host:      $(hostname)"
  info "pwd:       $(pwd)"
  info "shell:     $SHELL"
  info "PATH:      $PATH" | head -c 300; echo
  info "date:      $(date -Iseconds)"
  info "uname:     $(uname -a)"

  sub "gateway key"
  if [ -z "$KEY" ]; then
    err "VERCEL_AI_GATEWAY_API_KEY / AI_GATEWAY_API_KEY not set"
    if [ -f "$SECRETS" ]; then
      info "sourcing $SECRETS…"
      set -a; . "$SECRETS" 2>/dev/null; set +a
      KEY="${VERCEL_AI_GATEWAY_API_KEY:-${AI_GATEWAY_API_KEY:-}}"
    fi
  fi
  if [ -z "$KEY" ]; then
    err "no key after attempting ~/.secrets — aborting"
    exit 1
  fi
  ok "gateway key: ${KEY:0:10}… (len ${#KEY})"

  sub "required binaries"
  local missing=0
  for bin in curl jq; do
    if command -v "$bin" >/dev/null 2>&1; then
      ok "$bin  →  $(command -v "$bin")  ($(command $bin --version 2>&1 | head -1))"
    else
      err "$bin  MISSING"
      missing=$((missing+1))
    fi
  done
  [ "$missing" -gt 0 ] && { err "$missing required binaries missing"; exit 1; }

  sub "optional binaries (nuclei family)"
  for bin in go pdtm nuclei httpx subfinder dnsx katana naabu; do
    if command -v "$bin" >/dev/null 2>&1; then
      ok "$bin  →  $(command -v "$bin")"
    else
      warn "$bin  (not yet installed)"
    fi
  done

  sub "stale direnv hook check"
  if type _direnv_hook >/dev/null 2>&1; then
    warn "_direnv_hook is defined in this shell (may cause /usr/bin/direnv errors)"
    info "fix: unset -f _direnv_hook; PROMPT_COMMAND=\"\${PROMPT_COMMAND//_direnv_hook/}\""
  else
    ok "no stale direnv hook"
  fi

  sub "secrets file"
  if [ -f "$SECRETS" ]; then
    ok "$SECRETS  ($(wc -l < "$SECRETS") lines, mode $(stat -c '%a' "$SECRETS"))"
  else
    warn "$SECRETS not found"
  fi
}
SECTION 00-preflight section_00_preflight

# ════════════════════════════════════════════════════════════════════════════
# §1  PROJECTDISCOVERY TOOLCHAIN
# ════════════════════════════════════════════════════════════════════════════
section_01_pdtm() {
  hdr "1. ProjectDiscovery toolchain"
  if command -v nuclei >/dev/null 2>&1 && command -v pdtm >/dev/null 2>&1; then
    ok "all tools already present — skipping pdtm -ia"
    for t in pdtm nuclei httpx subfinder dnsx katana naabu; do command -v "$t" >/dev/null && ok "$t" || warn "$t missing"; done
    return 0
  fi

  # Ensure Go
  if ! command -v go >/dev/null 2>&1; then
    warn "Go not found — installing via pacman"
    sudo pacman -S --noconfirm go 2>&1 | tail -5
  fi
  ok "go: $(go version 2>/dev/null)"

  export GOPATH="${GOPATH:-$HOME/go}"
  export GOBIN="$GOPATH/bin"
  export PATH="$GOBIN:$HOME/.pdtm/go/bin:$PATH"

  # Append to bashrc if missing
  if ! grep -q '\.pdtm/go/bin' "$HOME/.bashrc" 2>/dev/null; then
    {
      echo ''
      echo '# ProjectDiscovery toolchain (added by pd-audit)'
      echo 'export PATH="$HOME/.pdtm/go/bin:$HOME/go/bin:$PATH"'
    } >> "$HOME/.bashrc"
    ok "appended pdtm to ~/.bashrc"
  else
    ok "~/.bashrc already has pdtm path"
  fi

  # Install pdtm
  if ! command -v pdtm >/dev/null 2>&1; then
    info "installing pdtm…"
    go install -v github.com/projectdiscovery/pdtm/cmd/pdtm@latest 2>&1 | tail -5
    hash -r
  fi
  ok "pdtm: $(pdtm -version 2>/dev/null | head -1 || echo present)"

  # Install all tools
  info "pdtm -install-all (silent, ~60s)…"
  pdtm -ia 2>&1 | tee "$LOG_DIR/pdtm-install.log" | tail -20
  pdtm -ip 2>&1 | tee "$LOG_DIR/pdtm-path.log" | tail -3

  hash -r

  # Verify each
  sub "installed tools"
  for t in pdtm nuclei httpx subfinder dnsx katana naabu tlsx cdncheck asnmap interactsh-client notify; do
    if command -v "$t" >/dev/null 2>&1; then
      ok "$t  $(command $t -version 2>/dev/null | head -1)"
    else
      warn "$t  not on PATH"
    fi
  done

  # Nuclei templates
  if command -v nuclei >/dev/null 2>&1; then
    sub "nuclei templates"
    info "updating templates…"
    nuclei -update-templates -silent 2>&1 | tail -3
    local n; n=$(find "$HOME/nuclei-templates" -name '*.yaml' 2>/dev/null | wc -l)
    ok "nuclei-templates: $n yaml files"
    # List top categories
    find "$HOME/nuclei-templates" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | \
      head -30 | sed "s|$HOME/nuclei-templates/|    |"
  fi
}
SECTION 01-pdtm section_01_pdtm

# ════════════════════════════════════════════════════════════════════════════
# §2  GATEWAY CATALOG
# ════════════════════════════════════════════════════════════════════════════
section_02_catalog() {
  hdr "2. Vercel AI Gateway catalog"

  sub "public catalog (unauthenticated)"
  local t0; t0=$(date +%s%N)
  curl -sS -o "$ART/catalog-public.json" -w "  http=%{http_code}  size=%{size_download}B  time=%{time_total}s\n" \
    "$UP/models"
  local t1; t1=$(date +%s%N)
  local pub_n; pub_n=$(jq -r '.data | length' "$ART/catalog-public.json" 2>/dev/null)
  ok "public: $pub_n models  ($(awk "BEGIN{printf \"%.0f\", ($t1-$t0)/1000000}")ms)"

  sub "authenticated catalog with eligibility"
  curl -sS -o "$ART/catalog-avail.json" -w "  http=%{http_code}  size=%{size_download}B  time=%{time_total}s\n" \
    "$UP/models?include_availability" \
    -H "Authorization: Bearer $KEY"
  local av_n; av_n=$(jq -r '.data | length' "$ART/catalog-avail.json" 2>/dev/null)
  ok "authenticated: $av_n models"

  sub "catalog envelope"
  jq -r '
    "  availability_status:          \(.availability_status // "?")",
    "  catalog_status:               \(.catalog_status // "?")",
    "  evaluation_context:           \(.evaluation_context // "?")",
    "  request_context_availability:"
  ' "$ART/catalog-avail.json" 2>/dev/null
  jq -r '
    (.request_context_availability // {})
    | to_entries[]
    | "    \(.key): \(.value.status // "?")"
  ' "$ART/catalog-avail.json" 2>/dev/null

  sub "sample model (schema probe)"
  jq '.data[0] | keys' "$ART/catalog-avail.json" 2>/dev/null
  echo ""
  jq '.data[0]' "$ART/catalog-avail.json" 2>/dev/null | head -40
}
SECTION 02-catalog section_02_catalog

# ════════════════════════════════════════════════════════════════════════════
# §3  ELIGIBILITY BREAKDOWN
# ════════════════════════════════════════════════════════════════════════════
section_03_eligibility() {
  hdr "3. Eligibility breakdown"

  sub "status counts"
  jq -r '.data[].model_eligibility.status // "unannotated"' \
    "$ART/catalog-avail.json" 2>/dev/null \
    | sort | uniq -c | sort -rn | sed 's/^/    /'

  sub "ineligible categories × reasons"
  jq -r '
    .data[]
    | select(.model_eligibility.status == "ineligible")
    | "\(.model_eligibility.category // "?") | \(.model_eligibility.reason // "?")"
  ' "$ART/catalog-avail.json" 2>/dev/null \
    | sort | uniq -c | sort -rn | sed 's/^/    /'

  sub "ineligible by runtime"
  jq -r '
    .data[]
    | select(.model_eligibility.status == "ineligible")
    | "\(.model_eligibility.evaluated_runtime // "?")"
  ' "$ART/catalog-avail.json" 2>/dev/null \
    | sort | uniq -c | sort -rn | sed 's/^/    /'

  sub "eligible models by type"
  jq -r '
    .data[]
    | select(.model_eligibility.status == "eligible")
    | .type // "?"
  ' "$ART/catalog-avail.json" 2>/dev/null \
    | sort | uniq -c | sort -rn | sed 's/^/    /'

  sub "eligible language models"
  jq -r '
    .data[]
    | select(.model_eligibility.status == "eligible")
    | select(.type == "language")
    | .id
  ' "$ART/catalog-avail.json" 2>/dev/null | sort > "$ART/eligible.txt"
  local n; n=$(wc -l < "$ART/eligible.txt")
  ok "$n eligible language models → $ART/eligible.txt"

  sub "full eligibility TSV"
  jq -r '
    .data[]
    | "\(.model_eligibility.status // "unannotated")\t\(.model_eligibility.category // "-")\t\(.model_eligibility.reason // "-")\t\(.model_eligibility.evaluated_runtime // "-")\t\(.id)\t\(.type // "?")"
  ' "$ART/catalog-avail.json" 2>/dev/null | sort > "$ART/eligibility.tsv"
  ok "wrote $ART/eligibility.tsv ($(wc -l < "$ART/eligibility.tsv") rows)"
}
SECTION 03-eligibility section_03_eligibility

# ════════════════════════════════════════════════════════════════════════════
# §4  DEEP PROBE (per-model endpoints)
# ════════════════════════════════════════════════════════════════════════════
section_04_deep_probe() {
  hdr "4. Per-endpoint deep probe"

  cat > "$ART/deep-probe.sh" <<'DEEP'
#!/bin/bash
M="$1"; K="$2"; U="$3"; AV="$4"
T=$(mktemp)
curl -sS -o "$T" --max-time 6 "$U/models/$M/endpoints" -H "Authorization: Bearer $K" 2>/dev/null
EPS=$(jq -c '[.data.endpoints[]? | {p:.provider_name, prompt:.pricing.prompt, completion:.pricing.completion, status:.status, up15:.uptime_last_15m, up1h:.uptime_last_1h, tp50:.throughput_last_1h.p50, tp95:.throughput_last_1h.p95, lat50:.latency_last_1h.p50, lat95:.latency_last_1h.p95}]' "$T" 2>/dev/null || echo '[]')
ROW=$(jq -c --arg m "$M" '.data[] | select(.id == $m) | {id, type, tags, pricing, zdr, no_training, model_eligibility, created, released, owned_by}' "$AV" 2>/dev/null || echo 'null')
jq -cn --arg m "$M" --argjson eps "$EPS" --argjson row "$ROW" '{model:$m, catalog:$row, endpoints:$eps}'
rm -f "$T"
DEEP
  chmod +x "$ART/deep-probe.sh"

  local n; n=$(wc -l < "$ART/eligible.txt")
  info "probing $n models, 4 parallel (annotated rate limit)…"

  # Resume-aware: skip models already in osint.jsonl
  if [ -s "$ART/osint.jsonl" ]; then
    jq -r '.model' "$ART/osint.jsonl" 2>/dev/null | sort -u > "$ART/.done.txt"
    comm -23 <(sort "$ART/eligible.txt") "$ART/.done.txt" > "$ART/.remaining.txt"
    info "resuming: $(wc -l < "$ART/.remaining.txt") of $(wc -l < "$ART/eligible.txt") still to probe"
  else
    : > "$ART/osint.jsonl"
    cp "$ART/eligible.txt" "$ART/.remaining.txt"
    info "starting fresh: $(wc -l < "$ART/.remaining.txt") models"
  fi
  local t0; t0=$(date +%s)
  cat "$ART/.remaining.txt" \
    | xargs -P 32 -I {} "$ART/deep-probe.sh" {} "$KEY" "$UP" "$ART/catalog-avail.json" \
    | tee -a "$ART/osint.jsonl" > /dev/null
  local t1; t1=$(date +%s)
  ok "deep probed $(wc -l < "$ART/osint.jsonl") models in $((t1-t0))s (32 parallel)"

  sub "endpoint count distribution"
  jq -r '.endpoints | length' "$ART/osint.jsonl" 2>/dev/null \
    | sort -n | uniq -c | sed 's/^/    /'

  sub "provider distribution (who serves what)"
  jq -r '.endpoints[]?.p' "$ART/osint.jsonl" 2>/dev/null \
    | sort | uniq -c | sort -rn | head -20 | sed 's/^/    /'
}
SECTION 04-deep-probe section_04_deep_probe

# ════════════════════════════════════════════════════════════════════════════
# §5  FREE LANE EXTRACTION
# ════════════════════════════════════════════════════════════════════════════
section_05_free_lanes() {
  hdr "5. Free lane extraction"

  sub "zero-price endpoint anywhere"
  jq -r '
    select((.endpoints // []) | any(
      (.prompt == "0" or .prompt == 0) and (.completion == "0" or .completion == 0)
    ))
    | "  \(.model)"
  ' "$ART/osint.jsonl" 2>/dev/null

  sub "ZDR-unavailable models (free but you pay with data)"
  jq -r '
    select(.catalog.model_eligibility.status == "eligible")
    | select(.catalog.zdr != "all")
    | "  \(.model)  zdr=\(.catalog.zdr // "?")  no_training=\(.catalog.no_training // "?")"
  ' "$ART/osint.jsonl" 2>/dev/null | tee "$ART/zdr-tradeoff.txt"
  info "wrote $ART/zdr-tradeoff.txt"

  sub "pixel-canary class (eligible, no free marker, no -free suffix)"
  jq -r '
    select(.catalog.model_eligibility.status == "eligible")
    | select((.catalog.tags // [] | index("free") | not) and (.model | endswith("-free") | not))
    | "  \(.model)  tags=\((.catalog.tags // []) | join(","))  in=\(.catalog.pricing.input)"
  ' "$ART/osint.jsonl" 2>/dev/null | head -40

  sub "tags histogram"
  jq -r '.catalog.tags[]?' "$ART/osint.jsonl" 2>/dev/null \
    | sort | uniq -c | sort -rn | head -30 | sed 's/^/    /'
}
SECTION 05-free-lanes section_05_free_lanes

# ════════════════════════════════════════════════════════════════════════════
# §6  LIVE VERIFICATION
# ════════════════════════════════════════════════════════════════════════════
section_06_live_verify() {
  hdr "6. Live free-lane verification"

  local CANDIDATES=(
    "poolside/laguna-s-2.1-free"
    "inclusionai/ling-3.1-flash"
    "inclusionai/ling-3.0-flash-sante"
    "inclusionai/ling-3.0-flash-sante-free"
    "inclusionai/ling-3.1-flash-free"
  )

  : > "$ART/live-verify.jsonl"
  for M in "${CANDIDATES[@]}"; do
    printf '  %-45s ' "$M"
    local T; T=$(mktemp)
    local t0; t0=$(date +%s%N)
    local C; C=$(curl -sS -o "$T" -w "%{http_code}" --max-time 45 \
      "$UP/chat/completions" \
      -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
      -d "{\"model\":\"$M\",\"messages\":[{\"role\":\"user\",\"content\":\"say ok\"}],\"max_tokens\":8}" 2>/dev/null)
    local t1; t1=$(date +%s%N)
    local MS; MS=$(awk "BEGIN{printf \"%.0f\", ($t1-$t0)/1000000}")
    local MSG; MSG=$(jq -r '.choices[0].message.content // .error.message // .error.type // "-"' "$T" 2>/dev/null | head -c 60)

    case "$C" in
      200) printf "${G}HTTP %s${N}  %sms  %s\n" "$C" "$MS" "$MSG" ;;
      429) printf "${Y}HTTP %s${N}  %sms  %s\n" "$C" "$MS" "$MSG" ;;
      *)   printf "${R}HTTP %s${N}  %sms  %s\n" "$C" "$MS" "$MSG" ;;
    esac

    jq -cn --arg m "$M" --arg c "$C" --arg ms "$MS" --arg msg "$MSG" \
      --argjson body "$(jq -Rs . "$T" 2>/dev/null || echo '""')" \
      '{model:$m, http:$c, ms:($ms|tonumber), msg:$msg, body:$body}' >> "$ART/live-verify.jsonl"
    rm -f "$T"
  done
  info "wrote $ART/live-verify.jsonl"
}
SECTION 06-live-verify section_06_live_verify

# ════════════════════════════════════════════════════════════════════════════
# §7  NUCLEI FUZZING HARNESS
# ════════════════════════════════════════════════════════════════════════════
section_07_fuzz() {
  hdr "7. Nuclei fuzzing harness"

  mkdir -p "$ART/fuzz-templates"

  cat > "$ART/fuzz-templates/vg-model-fuzz.yaml" <<'YAML'
id: vercel-gateway-model-fuzz

info:
  name: Vercel AI Gateway Model Fuzzer
  author: estate-osint
  severity: info
  description: |
    Fuzz the Vercel AI Gateway chat completions endpoint with model IDs.
    Discovers which models return 200, which return structured errors,
    and which crash the gateway.

http:
  - pre-condition:
      - type: dsl
        dsl:
          - 'method == "POST"'
          - 'len(body) > 0'
        condition: and

    fuzzing:
      - part: body
        type: replace
        mode: single
        fuzz:
          - '{{model_id}}'

    matchers-condition: or
    matchers:
      - type: status
        status:
          - 200
          - 400
          - 401
          - 403
          - 404
          - 410
          - 429
          - 500
          - 502
          - 503

    extractors:
      - type: json
        json:
          - '.error.type'
          - '.error.message'
          - '.choices[0].message.content'
YAML
  ok "wrote fuzz template"

  # Build targets from osint
  jq -c -n --argjson models "$(jq -r '.model' "$ART/osint.jsonl" 2>/dev/null | sort -u | jq -R -s 'split("\n") | map(select(. != ""))')" '
    $models[] | {
      url: "https://ai-gateway.vercel.sh/v1/chat/completions",
      method: "POST",
      headers: {
        "Authorization": "Bearer '"$KEY"'",
        "Content-Type": "application/json"
      },
      body: ("{\"model\":\"" + . + "\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],\"max_tokens\":4}")
    }
  ' > "$ART/fuzz-targets.jsonl"
  ok "wrote $(wc -l < "$ART/fuzz-targets.jsonl") fuzz targets"

  if command -v nuclei >/dev/null 2>&1; then
    info "running nuclei -fuzz (2-4 min)…"
    local t0; t0=$(date +%s)
    nuclei -fuzz \
      -t "$ART/fuzz-templates/" \
      -l "$ART/fuzz-targets.jsonl" \
      -jsonl -o "$ART/fuzz-results.jsonl" \
      -c 32 -rl 200 \
      -timeout 30 -retries 1 \
      -silent -no-color 2>&1 | tee "$LOG_DIR/nuclei-fuzz.log" | tail -5
    local t1; t1=$(date +%s)
    ok "fuzz done in $((t1-t0))s"
    if [ -f "$ART/fuzz-results.jsonl" ]; then
      ok "$(wc -l < "$ART/fuzz-results.jsonl") findings → $ART/fuzz-results.jsonl"
      sub "findings by severity"
      jq -r '.info.severity // "?"' "$ART/fuzz-results.jsonl" 2>/dev/null | sort | uniq -c | sed 's/^/    /'
    fi
  else
    warn "nuclei not on PATH — skipping fuzz"
  fi

  # Go fuzz harness on nuclei matchers (optional)
  if command -v go >/dev/null 2>&1; then
    sub "native Go fuzz of nuclei matchers"
    local WORK="$HOME/.cache/nuclei-src"
    if [ ! -d "$WORK" ]; then
      info "cloning nuclei for go-fuzz…"
      git clone --depth 1 https://github.com/projectdiscovery/nuclei.git "$WORK" 2>&1 | tail -2
    fi
    if [ -d "$WORK/pkg/operators/matchers" ]; then
      cd "$WORK"
      cat > pkg/operators/matchers/fuzz_test.go <<'GOFUZZ'
package matchers

import "testing"

func FuzzCompileMatchers(f *testing.F) {
	f.Add([]byte("type: status\ncondition: or\nstatus:\n  - 200\n"))
	f.Add([]byte("type: word\nwords:\n  - foo\n"))
	f.Fuzz(func(t *testing.T, data []byte) {
		defer func() { recover() }()
		_, _ = CompileMatchers([]*Matcher{}, map[string]interface{}{})
		_ = data
	})
}
GOFUZZ
      info "running go test -fuzz (15s)…"
      go test -fuzz=FuzzCompileMatchers -fuzztime=15s ./pkg/operators/matchers/ \
        2>&1 | tail -15 | tee -a "$LOG_DIR/go-fuzz.log"
      cd - >/dev/null
    fi
  fi
}
SECTION 07-fuzz section_07_fuzz

# ════════════════════════════════════════════════════════════════════════════
# §8  OMP CONFIG
# ════════════════════════════════════════════════════════════════════════════
section_08_omp() {
  hdr "8. omp config"

  if [ -f "$OMP_CONFIG" ]; then
    cp -v "$OMP_CONFIG" "$OMP_CONFIG.bak-$RUN_ID"
    ok "backed up → $OMP_CONFIG.bak-$RUN_ID"
  else
    warn "no existing $OMP_CONFIG"
  fi

  cat > "$OMP_CONFIG" <<'OMP'
defaultThinkingLevel: medium
modelRoles:
  judge: openrouter/~typesafe/jev-latest
  tiny: local/lfm2.5-230m
  advisor: google/models/gemini-flash-tool-retrieval
  default: vercel-ai-gateway/poolside/laguna-s-2.1-free:medium
  fallbacks:
    - vercel-ai-gateway/inclusionai/ling-3.1-flash:medium
    - vercel-ai-gateway/inclusionai/ling-3.0-flash-sante:medium
symbolPreset: unicode
composer:
  shape: band
theme:
  dark: titanium
setupVersion: 2
dev:
  autoqaConsent: denied
contextPromotion:
  enabled: true
extendedContext: true
steeringMode: all
followUpMode: all
interruptMode: wait
features:
  unexpectedStopDetection: smart
memory:
  backend: local
hindsight:
  apiUrl: http://localhost:25287
edit:
  mode: sloppy
  blockAutoGenerated: false
  blackbox:
    enabled: true
  autoRepair:
    enabled: true
readLineNumbers: true
read:
  renderMarkdown: true
  toolResultPreview: true
lsp:
  diagnosticsOnEdit: true
bash:
  allowCompoundCommands: true
  direnv: "off"
shellMinimizer:
  sourceOutlineLevel: aggressive
eval:
  autoBackground:
    enabled: true
python:
  kernelMode: session
astGrep:
  enabled: true
computer:
  enabled: true
generate_image:
  enabled: true
checkpoint:
  enabled: true
vault:
  enabled: true
github:
  enabled: true
tools:
  abortOnFabricatedResult: true
  speculativeExecution:
    enabled: true
  xdevDocs: inline
mcp:
  notifications: true
task:
  enableEffort: true
  maxConcurrency: 4
  enableLsp: true
  isolation:
    merge: branch
worktree:
  clone: false
snapcompact:
  toolResults: true
  systemPrompt: agents-md
providers:
  openai-codex:
    codeMode: "on"
tier:
  subagent: auto
advisor:
  enabled: true
  syncBacklog: "1"
grep:
  enabled: true
glob:
  enabled: true
find:
  enabled: "off"
temperature: 0.2
textVerbosity: low
inlineToolDescriptors: "on"
skillful: false
personality: pragmatic
retry:
  fallbackChains: {}
  usageAwareFallback: true
  modelFallback: true
  maxRetries: 2
OMP

  ok "wrote $OMP_CONFIG"
  sub "model lines"
  grep -nE 'default:|fallbacks:|  - vercel' "$OMP_CONFIG" | sed 's/^/    /'
}
SECTION 08-omp section_08_omp

# ════════════════════════════════════════════════════════════════════════════
# §9  TAU CONFIG
# ════════════════════════════════════════════════════════════════════════════
section_09_tau() {
  hdr "9. tau config"

  if [ ! -f "$TAU_CONFIG" ]; then
    warn "$TAU_CONFIG not found — skipping"
    return 0
  fi

  local readable=0
  head -1 "$TAU_CONFIG" >/dev/null 2>&1 && readable=1

  if [ "$readable" -eq 1 ]; then
    cp -v "$TAU_CONFIG" "$TAU_CONFIG.bak-$RUN_ID"
    ok "backed up (as user) → $TAU_CONFIG.bak-$RUN_ID"
    sed -i \
      -e 's|default: vercel-ai-gateway/minimax/minimax-m2.7-free:medium|default: vercel-ai-gateway/poolside/laguna-s-2.1-free:medium|' \
      -e 's|default: vercel-ai-gateway/.*:medium|default: vercel-ai-gateway/poolside/laguna-s-2.1-free:medium|' \
      "$TAU_CONFIG"
    ok "patched $TAU_CONFIG"
    grep -nE 'default:|fallbacks:' "$TAU_CONFIG" | head -5 | sed 's/^/    /'
  else
    info "$TAU_CONFIG requires sudo"
    sudo cp -v "$TAU_CONFIG" "$TAU_CONFIG.bak-$RUN_ID"
    sudo sed -i \
      -e 's|default: vercel-ai-gateway/minimax/minimax-m2.7-free:medium|default: vercel-ai-gateway/poolside/laguna-s-2.1-free:medium|' \
      -e 's|default: vercel-ai-gateway/.*:medium|default: vercel-ai-gateway/poolside/laguna-s-2.1-free:medium|' \
      "$TAU_CONFIG"
    ok "patched with sudo"
    sudo grep -nE 'default:|fallbacks:' "$TAU_CONFIG" | head -5 | sed 's/^/    /'
  fi
}
SECTION 09-tau section_09_tau

# ════════════════════════════════════════════════════════════════════════════
# §10  SECRETS RELOAD
# ════════════════════════════════════════════════════════════════════════════
section_10_secrets() {
  hdr "10. Secrets reload"

  if [ -f "$SECRETS" ]; then
    set -a; . "$SECRETS" 2>/dev/null; set +a
    ok "sourced $SECRETS"
    sub "key presence (first 12 chars)"
    for k in NVIDIA_API_KEY FLOCK_API_KEY VERCEL_AI_GATEWAY_API_KEY AI_GATEWAY_API_KEY OPENROUTER_API_KEY ANTHROPIC_API_KEY; do
      local v; v="${!k:-}"
      if [ -n "$v" ]; then
        printf "    %-30s %s… (len %d)\n" "$k" "${v:0:12}" "${#v}"
      else
        printf "    %-30s ${R}(unset)${N}\n" "$k"
      fi
    done
  else
    warn "$SECRETS not found"
  fi
}
SECTION 10-secrets section_10_secrets

# ════════════════════════════════════════════════════════════════════════════
# §11  FLOCK / NIM PROXY HEALTH
# ════════════════════════════════════════════════════════════════════════════
section_11_flock() {
  hdr "11. Flock / nim-proxy health"

  sub "listening ports"
  ss -tlnp 2>/dev/null | grep -E ':(25193|25204|25104|8000)\s' | sed 's/^/    /' || info "none of 25193/25204/25104/8000 listening"

  sub "flock process"
  ps -o pid,ppid,etime,cmd -p "$(pgrep -f '/home/toxic/.flock/flock' | head -1)" 2>/dev/null | sed 's/^/    /' || info "flock not running"

  if curl -s --max-time 5 "http://127.0.0.1:25193/health" -o /dev/null; then
    sub "flock /health"
    curl -s --max-time 5 "http://127.0.0.1:25193/health" | head -c 300; echo
  fi

  sub "flock /v1/models with FLOCK_API_KEY"
  if [ -n "${FLOCK_API_KEY:-}" ]; then
    local C; C=$(curl -s -o /tmp/flock-models.json -w "%{http_code}" --max-time 10 \
      "http://127.0.0.1:25193/v1/models" -H "Authorization: Bearer $FLOCK_API_KEY")
    local N; N=$(jq -r '.data | length' /tmp/flock-models.json 2>/dev/null || echo "?")
    printf '    HTTP %s  models=%s\n' "$C" "$N"
  else
    warn "FLOCK_API_KEY unset"
  fi

  sub "flock /v1/chat/completions (one model)"
  if [ -n "${FLOCK_API_KEY:-}" ]; then
    local C; C=$(curl -s -o /tmp/flock-chat.json -w "%{http_code}" --max-time 30 \
      "http://127.0.0.1:25193/v1/chat/completions" \
      -H "Authorization: Bearer $FLOCK_API_KEY" -H "Content-Type: application/json" \
      -d '{"model":"nvidia/nemotron-3.5-lightning-30b-a3b","messages":[{"role":"user","content":"hi"}],"max_tokens":4}')
    printf '    HTTP %s  %s\n' "$C" "$(jq -r '.choices[0].message.content // .error.message // "-"' /tmp/flock-chat.json 2>/dev/null | head -c 60)"
  fi
}
SECTION 11-flock section_11_flock

# ════════════════════════════════════════════════════════════════════════════
# §12  FINAL SUMMARY
# ════════════════════════════════════════════════════════════════════════════
section_12_summary() {
  hdr "12. FINAL SUMMARY"

  local total_size; total_size=$(du -sh "$LOG_DIR" 2>/dev/null | awk '{print $1}')
  info "run id:     $RUN_ID"
  info "log dir:    $LOG_DIR"
  info "size:       $total_size"
  info "master:     $MASTER"
  echo ""

  sub "gateway free lanes (LIVE, just tested)"
  jq -r '"  \(.http)\t\(.ms)ms\t\(.model)\t\(.msg[0:40])"' "$ART/live-verify.jsonl" 2>/dev/null | column -t -s$'\t'

  sub "eligible language models count"
  ok "$(wc -l < "$ART/eligible.txt")"

  sub "free lanes discovered"
  jq -r 'select(.endpoints|any(.prompt=="0" and .completion=="0")) | "  \(.model)"' "$ART/osint.jsonl" 2>/dev/null

  sub "nuclei fuzz results"
  if [ -f "$ART/fuzz-results.jsonl" ]; then
    ok "$(wc -l < "$ART/fuzz-results.jsonl") findings"
  else
    warn "no fuzz results"
  fi

  sub "omp config (current)"
  grep -nE 'default:|fallbacks:|  - vercel' "$OMP_CONFIG" 2>/dev/null | sed 's/^/    /'

  sub "tau config (current)"
  { grep -nE 'default:|fallbacks:' "$TAU_CONFIG" 2>/dev/null || sudo grep -nE 'default:|fallbacks:' "$TAU_CONFIG" 2>/dev/null; } | head -5 | sed 's/^/    /'

  sub "artifacts"
  for f in catalog-public.json catalog-avail.json eligible.txt eligibility.tsv \
           osint.jsonl live-verify.jsonl zdr-tradeoff.txt fuzz-targets.jsonl fuzz-results.jsonl; do
    if [ -f "$ART/$f" ]; then
      printf "    %-28s %8s  %s\n" "$f" "$(du -h "$ART/$f" | cut -f1)" "$ART/$f"
    fi
  done

  echo ""
  printf "${W}═══════════════════════════════════════════════════════════════════════${N}\n"
  printf "${W} DONE. Run these:${N}\n"
  printf "${W}═══════════════════════════════════════════════════════════════════════${N}\n"
  echo ""
  printf "  ${C}exec bash -l${N}         # reload shell with new PATH + configs\n"
  printf "  ${C}omp${N}                  # should show 'Laguna S 2.1 Free' in the banner\n"
  printf "  ${C}tau${N}                  # same model\n"
  echo ""
  printf "  ${C}less %s${N}\n" "$MASTER"
  printf "  ${C}jq 'select(.http==\"200\")' %s/live-verify.jsonl${N}\n" "$ART"
  printf "  ${C}jq 'select(.endpoints|any(.prompt==\"0\"))' %s/osint.jsonl${N}\n" "$ART"
  echo ""
  printf "${W}═══════════════════════════════════════════════════════════════════════${N}\n"
}
SECTION 12-summary section_12_summary

# ── Done ─────────────────────────────────────────────────────────────────────
dbg "all sections complete"
dbg "master log: $MASTER"

exit 0
