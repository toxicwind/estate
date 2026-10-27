#!/usr/bin/env bash
set -euo pipefail

# ─── CONFIG ──────────────────────────────────────────────────────────────
: "${FREEINFERENCE_API_KEY:?Set FREEINFERENCE_API_KEY to your hyi- key}"
FI_SESSION_JWT="${FI_SESSION_JWT:-}" # Optional: Bearer eyJ... from browser DevTools for /user/* routes
BASE="https://freeinference.org"
DATA_BASE="https://openinfra.freeinference.org"
OUT="/tmp/fi_orthogonal/out"
SESSION_ID="probe-$(date -u +%Y%m%d-%H%M%S)"
mkdir -p "$OUT"

# Site bans fake/missing user agents (banner 2026-07-30). Use a real browser UA everywhere.
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"

log() { printf '\n[%s] %s\n' "$(date -u +%H:%M:%SZ)" "$*"; }

# Data-plane helper (/v1/* and /anthropic/* use hyi-... API key)
req_v1() {
  curl -sS --compressed -A "$UA" \
    -H "Authorization: Bearer ${FREEINFERENCE_API_KEY}" \
    -H "X-Session-ID: ${SESSION_ID}" \
    -H "Content-Type: application/json" "$@"
}

# Control-plane helper (/user/* uses session JWT if set, otherwise falls back to API key to show 401 vs 200 split)
req_user() {
  local tok="${FI_SESSION_JWT:-$FREEINFERENCE_API_KEY}"
  curl -sS --compressed -A "$UA" \
    -H "Authorization: Bearer ${tok}" \
    -H "Accept: application/json" "$@"
}

# ─── 1. CONTROL-PLANE, SITE-UPDATES & ULID CHRONOMETRY ───────────────────
log "1. Probing /site-updates, /auth/accounts, /user/me, /user/usage, /user/api-keys/all"
curl -sS --compressed -A "$UA" -H "Accept: application/json" "${BASE}/site-updates" | tee "$OUT/site_updates.json" || true
req_user "${BASE}/auth/accounts" | tee "$OUT/accounts.json" || true
req_user "${BASE}/user/me" | tee "$OUT/me.json" || true
req_user "${BASE}/user/usage?period=today" | tee "$OUT/usage.json" || true
req_user "${BASE}/user/api-keys/all" | tee "$OUT/api_keys_all.json" || true

if [[ -n "$FI_SESSION_JWT" ]]; then
  log "1b. Decoding Crockford Base32 ULIDs (sub, sid, jti) from FI_SESSION_JWT"
  python3 - "$FI_SESSION_JWT" << 'PYEOF' | tee "$OUT/jwt_ulids.json"
import base64, datetime, json, sys
CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
def ulid_ts(u: str):
    s = u.split("_")[-1]
    if len(s) < 10 or any(c not in CROCKFORD for c in s[:10]): return None
    ms = 0
    for c in s[:10]: ms = ms * 32 + CROCKFORD.index(c)
    return {"id": u, "epoch_ms": ms, "utc": datetime.datetime.fromtimestamp(ms/1000, tz=datetime.timezone.utc).isoformat()}
parts = sys.argv[1].split(".")
if len(parts) >= 2:
    p = json.loads(base64.urlsafe_b64decode(parts[1] + "==").decode())
    print(json.dumps({"role": p.get("role"), "ttl_s": int(p.get("exp",0)) - int(p.get("iat",0)), "ulids": {k: ulid_ts(str(p.get(k,""))) for k in ("sub","sid","jti")}}, indent=2))
PYEOF
fi

# ─── 2. /v1/models HEADER POLYMORPHISM & ROUTE BOUNDARIES ────────────────
log "2. Testing /v1/models schema switch (OpenAI default vs Anthropic-Version: 2023-06-01)"
req_v1 "${BASE}/v1/models" > "$OUT/models_openai.json"
curl -sS --compressed -A "$UA" \
  -H "Authorization: Bearer ${FREEINFERENCE_API_KEY}" \
  -H "Anthropic-Version: 2023-06-01" \
  "${BASE}/v1/models" > "$OUT/models_anthropic.json" || true

jq -r '.data[].id' "$OUT/models_openai.json" 2>/dev/null | tee "$OUT/model_ids.txt" || true

log "2a. Diffing OpenAI vs Anthropic model lists (polymorphism wire diff)"
python3 - "$OUT/models_openai.json" "$OUT/models_anthropic.json" << 'PYEOF' | tee "$OUT/models_polymorphism_diff.json"
import json, sys
def load(p):
    raw = open(p).read().strip()
    try: return json.loads(raw) if raw else {}
    except Exception: return {}
o, a = load(sys.argv[1]), load(sys.argv[2])
oai = {m["id"] for m in o.get("data", [])}
anth = {m["id"] for m in a.get("data", [])}
print(json.dumps({
    "openai_schema_count": len(oai),
    "anthropic_schema_count": len(anth),
    "only_in_openai_schema": sorted(oai - anth),
    "only_in_anthropic_schema": sorted(anth - oai),
    "anthropic_sample": (a.get("data") or [{}])[0],
}, indent=2))
PYEOF

log "2b. Testing doc-label 'glm-5.3' (404) vs actual ID 'glm-5.3-flash' (200) vs 'bge-m3' on chat route (404)"
req_v1 -X POST "${BASE}/v1/chat/completions" \
  -d '{"model":"glm-5.3","messages":[{"role":"user","content":"ping"}],"max_tokens":1}' | tee "$OUT/glm53_doclabel.json" || true
req_v1 -X POST "${BASE}/v1/chat/completions" \
  -d '{"model":"glm-5.3-flash","messages":[{"role":"user","content":"ping"}],"max_tokens":1}' | tee "$OUT/glm53_flash.json" || true
req_v1 -X POST "${BASE}/v1/chat/completions" \
  -d '{"model":"bge-m3","messages":[{"role":"user","content":"ping"}],"max_tokens":1}' | tee "$OUT/bgem3_chat_reject.json" || true
req_v1 -X POST "${BASE}/v1/embeddings" \
  -d '{"model":"bge-m3","input":"ping"}' | jq '{object, model, dim: (.data[0].embedding | length)}' | tee "$OUT/bgem3_embed_ok.json" || true

# ─── 3. ANTHROPIC MESSAGES WIRE TRANSLATOR (/anthropic/v1/messages) ──────
log "3. Probing Anthropic wire translator (/anthropic/v1/messages with anthropic-version: 2023-06-01)"
curl -sS --compressed -A "$UA" -X POST "${BASE}/anthropic/v1/messages" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${FREEINFERENCE_API_KEY}" \
  -H "anthropic-version: 2023-06-01" \
  -H "X-Session-ID: ${SESSION_ID}" \
  -d '{"model":"minimax-m3","max_tokens":16,"messages":[{"role":"user","content":"Say ok."}]}' | tee "$OUT/anthropic_minimax.json" || true

# ─── 4. X-REASONING-PASSTHROUGH & ECHOED X-REQUEST-ID WIRE DIFF ──────────
log "4. Probing X-Reasoning-Passthrough (default passthrough vs 'false' strip mode) + X-Request-ID echo"
REQ_ID_BASE="req-$(date +%s)"
curl -sS -D "$OUT/hdr_reasoning_on.txt" --compressed -X POST "${BASE}/v1/chat/completions" \
  -H "Authorization: Bearer ${FREEINFERENCE_API_KEY}" \
  -H "X-Session-ID: ${SESSION_ID}" \
  -H "X-Request-ID: ${REQ_ID_BASE}-on" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"2+2?"}],"max_tokens":32}' > "$OUT/reasoning_on.json" || true

curl -sS -D "$OUT/hdr_reasoning_off.txt" --compressed -X POST "${BASE}/v1/chat/completions" \
  -H "Authorization: Bearer ${FREEINFERENCE_API_KEY}" \
  -H "X-Session-ID: ${SESSION_ID}" \
  -H "X-Request-ID: ${REQ_ID_BASE}-off" \
  -H "X-Reasoning-Passthrough: false" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"2+2?"}],"max_tokens":32}' > "$OUT/reasoning_off.json" || true

python3 - "$OUT/reasoning_on.json" "$OUT/reasoning_off.json" << 'PYEOF' | tee "$OUT/reasoning_diff.json"
import json, sys
r_on = json.load(open(sys.argv[1])) if open(sys.argv[1]).read().strip() else {}
r_off = json.load(open(sys.argv[2])) if open(sys.argv[2]).read().strip() else {}
msg_on = (r_on.get("choices") or [{}])[0].get("message") or {}
msg_off = (r_off.get("choices") or [{}])[0].get("message") or {}
print(json.dumps({
    "passthrough_default_message_keys": list(msg_on.keys()),
    "passthrough_false_message_keys": list(msg_off.keys()),
    "usage_on": r_on.get("usage"),
    "usage_off": r_off.get("usage"),
}, indent=2))
PYEOF

# ─── 5. HIDDEN TELEMETRY FIELDS & 16-TOKEN o200k_base BLOCK ALIGNMENT ────
log "5. Auditing /user/recent-requests for provider split, routewise, and 16-token cache block alignment"
req_user "${BASE}/user/recent-requests?limit=20&offset=0" > "$OUT/recent_requests.json" || true

python3 - "$OUT/recent_requests.json" << 'PYEOF' | tee "$OUT/recent_requests_audit.json"
import json, sys
raw = open(sys.argv[1]).read().strip()
data = json.loads(raw) if raw else {}
rows = data.get("requests") or data.get("data") or (data if isinstance(data, list) else [])
providers = {}
non_16_aligned = []
for r in rows:
    if not isinstance(r, dict): continue
    p = str(r.get("provider") or "unknown")
    providers[p] = providers.get(p, 0) + 1
    c_tok = int(r.get("cache_read_tokens") or 0)
    if c_tok > 0 and (c_tok % 16 != 0):
        non_16_aligned.append({"id": r.get("id"), "cache_read_tokens": c_tok, "mod_16": c_tok % 16})
print(json.dumps({
    "rows_inspected": len(rows),
    "provider_distribution": providers,
    "all_cached_reads_16_token_aligned": len(non_16_aligned) == 0,
    "non_16_aligned_exceptions": non_16_aligned,
}, indent=2))
PYEOF

# ─── 5b. PUBLIC STATS (unauthenticated usage/model reveal) ────────────────
log "5b. Pulling /public-stats (model usage incl. unlisted models, agent products, totals)"
curl -sS --compressed -A "$UA" -H "Accept: application/json" "${BASE}/public-stats" > "$OUT/public_stats.json" || echo "{}" > "$OUT/public_stats.json"
python3 - "$OUT/public_stats.json" << 'PYEOF' | tee "$OUT/public_stats_summary.json"
import json, sys
raw = open(sys.argv[1]).read().strip()
try: d = json.loads(raw) if raw else {}
except Exception: d = {}
models = d.get("models") or {}
print(json.dumps({
    "listed_models": [{"name": m.get("name"), "tokens_T": round((m.get("tokens") or 0)/1e12, 3),
                       "requests_M": round((m.get("requests") or 0)/1e6, 2)}
                      for m in models.get("items", [])],
    "unlisted_other_tokens_T": round((models.get("other", {}).get("tokens") or 0)/1e12, 3),
    "unlisted_other_requests": models.get("other", {}).get("requests"),
    "totals_tokens_T": round((d.get("totals", {}).get("tokens") or 0)/1e12, 3),
    "totals_accounts": d.get("totals", {}).get("accounts"),
    "cached_input_share": d.get("totals", {}).get("cached_input_share"),
    "registrations": d.get("registrations"),
    "top_products": [{"name": p.get("name"), "kind": p.get("kind"), "tokens_T": round((p.get("tokens") or 0)/1e12, 3)}
                     for p in (d.get("agents", {}).get("products") or [])[:10]],
    "window": d.get("window"),
}, indent=2))
PYEOF

# ─── 6. OPENINFRA LIVE DCGM, HICACHE & SPECULATIVE DECODING TELEMETRY ────
log "6. Pulling live OpenInfra DCGM GPU & SGLang speculative-decoding snapshot (/api/dashboard)"
curl -sS --compressed -A "$UA" -H "Accept: application/json" "${DATA_BASE}/api/dashboard" > "$OUT/openinfra_dashboard.json" 2>/dev/null || echo "{}" > "$OUT/openinfra_dashboard.json"
curl -sS --compressed -A "$UA" -H "Accept: application/json" "${DATA_BASE}/api/history?hours=2" > "$OUT/openinfra_history_2h.json" 2>/dev/null || echo "{}" > "$OUT/openinfra_history_2h.json"

python3 - "$OUT/openinfra_dashboard.json" "$OUT/openinfra_history_2h.json" << 'PYEOF' | tee "$OUT/openinfra_summary.json"
import json, sys
def load(p):
    raw = open(p).read().strip()
    try: return json.loads(raw) if raw else {}
    except Exception: return {}
dash = load(sys.argv[1])
h = load(sys.argv[2])
# Summary prefers the LIVE history payload (dashboard may be empty/0B);
# history = {grain_ms, gpu[], sglang[], cpu[], generated_at, from_cache}
src = h if isinstance(h, dict) and h.get("gpu") else (dash if isinstance(dash, dict) else {})
gpus = src.get("gpu") or []
srvs = src.get("sglang") or []
nodes_gpu = sorted({r.get("node_id") for r in gpus if isinstance(r, dict)})
servers = sorted({r.get("server_id") for r in srvs if isinstance(r, dict)})
latest_gpu, latest_srv = {}, {}
for r in gpus:
    if isinstance(r, dict): latest_gpu[r.get("gpu_id")] = r
for r in srvs:
    if isinstance(r, dict): latest_srv[r.get("server_id")] = r
print(json.dumps({
    "source": "history" if src is h else ("dashboard" if src else "none"),
    "top_level_keys": sorted(src.keys()) if isinstance(src, dict) else [],
    "grain_ms": src.get("grain_ms"),
    "generated_at": src.get("generated_at"),
    "gpu_nodes": nodes_gpu,
    "sglang_servers": servers,
    "gpu_rows": len(gpus), "sglang_rows": len(srvs), "cpu_rows": len(src.get("cpu") or []),
    "latest_gpu": [{"gpu_id": k, "util_pct": v.get("utilization_pct"), "mem_pct": v.get("memory_pct"),
                    "temp_c": v.get("temperature_c"), "power_w": v.get("power_w")} for k, v in sorted(latest_gpu.items())],
    "latest_servers": [{"server_id": k, "running": v.get("running"), "queued": v.get("queued"),
                        "gen_tps": v.get("gen_throughput"), "ttft_s": v.get("ttft_avg_s"),
                        "cache_hit": v.get("cache_hit_rate"),
                        "hicache": [v.get("hicache_host_used"), v.get("hicache_host_total")],
                        "spec_accept_len": v.get("spec_accept_length")} for k, v in sorted(latest_srv.items())],
}, indent=2))
PYEOF

# ─── 7. COMPILE SUMMARY REPORT ───────────────────────────────────────────
log "7. Writing consolidated report to $OUT/anomaly_report.md"
{
  echo "# FreeInference Build 4b80416 Orthogonal Probe Report"
  echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo
  echo "## 1. Site Updates & Quota Plane"
  echo '```json'
  cat "$OUT/site_updates.json" 2>/dev/null || echo "{}"
  echo
  cat "$OUT/usage.json" 2>/dev/null || echo "{}"
  echo '```'
  echo
  echo "## 2. /v1/models OpenAI vs Anthropic-Version Polymorphism"
  echo '```json'
  cat "$OUT/models_polymorphism_diff.json" 2>/dev/null || echo "{}"
  echo '```'
  echo
  echo "## 3. Anthropic Wire Translator (/anthropic/v1/messages)"
  echo '```json'
  cat "$OUT/anthropic_minimax.json" 2>/dev/null || echo "{}"
  echo '```'
  echo
  echo "## 4. X-Reasoning-Passthrough Wire Diff"
  echo '```json'
  cat "$OUT/reasoning_diff.json" 2>/dev/null || echo "{}"
  echo '```'
  echo
  echo "## 5. Recent Requests Provider Split & 16-Token Block Alignment"
  echo '```json'
  cat "$OUT/recent_requests_audit.json" 2>/dev/null || echo "{}"
  echo '```'
  echo
  echo "## 5b. Public Stats (models incl. unlisted, agents, totals)"
  echo '```json'
  cat "$OUT/public_stats_summary.json" 2>/dev/null || echo "{}"
  echo '```'
  echo
  echo "## 6. OpenInfra DCGM & SGLang Snapshot"
  echo '```json'
  cat "$OUT/openinfra_summary.json" 2>/dev/null || echo "{}"
  echo '```'
} > "$OUT/anomaly_report.md"

log "Done. Report written to $OUT/anomaly_report.md"
