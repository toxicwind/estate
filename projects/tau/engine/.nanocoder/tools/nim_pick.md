---
name: nim_pick
description: Pick the best NIM model for a role from community benchmarks + availability.
parameters:
  role:
    type: string
    enum: [fast, smart, plan]
    default: smart
approval: never
read_only: true
timeout_ms: 30000
---

python3 - <<'PY'
import json, urllib.request, os
role = "{{ role }}".strip() or "smart"
CAT = {"fast":"speed","smart":"balanced","plan":"intelligence"}[role]
NS = "https://nimstats.maurodruwel.be"
url = f"{NS}/top" if CAT == "balanced" else f"{NS}/top/{CAT}"
try:
    with urllib.request.urlopen(url, timeout=15) as r: b = json.load(r)
    print(json.dumps({"role": role, "model": b.get("best_model"), "score": b.get("score")}, indent=2))
except Exception as e:
    print(json.dumps({"error": str(e)}))
PY
