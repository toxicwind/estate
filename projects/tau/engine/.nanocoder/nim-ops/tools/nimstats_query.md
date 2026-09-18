name: nimstats_query
description: Query NIMStats hourly leaderboards. Returns the best model for a role with score and metrics.
parameters:
  role:
    type: string
    description: "fast (speed) | smart (balanced) | plan (intelligence)"
    enum: [fast, smart, plan]
    default: smart
approval: never
read_only: true
timeout_ms: 30000
python3 - <<'PY'
import json, urllib.request
role = "{{ role }}".strip() or "smart"
CAT = {"fast":"speed","smart":"balanced","plan":"intelligence"}[role]
NS = "https://nimstats.maurodruwel.be"
url = f"{NS}/top" if CAT == "balanced" else f"{NS}/top/{CAT}"
def get(u):
    try:
        with urllib.request.urlopen(u, timeout=15) as r: return json.load(r)
    except Exception as e: return {"error": str(e)}
b = get(url)
print(json.dumps({
    "role": role, "category": CAT,
    "best_model": b.get("best_model"),
    "score": b.get("score"),
    "intelligence": b.get("intelligence"),
    "uptime_pct": b.get("uptime"),
    "avg_response_ms": b.get("avg_response_time_ms"),
    "avg_ttft_ms": b.get("avg_time_to_first_token_ms"),
    "avg_throughput_tps": b.get("avg_throughput_tps"),
    "last_seen": b.get("last_seen"),
}, indent=2))
PY
