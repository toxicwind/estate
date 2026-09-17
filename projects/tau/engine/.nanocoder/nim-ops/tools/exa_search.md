name: exa_search
description: Web search via Exa. Uses advanced search if EXA_API_KEY is set.
parameters:
  query:
    type: string
    description: Search query
    required: true
  num_results:
    type: integer
    description: Max results
    default: 6
approval: never
read_only: true
timeout_ms: 30000
python3 - <<'PY'
import json, os, urllib.request
key = os.environ.get("EXA_API_KEY")
if not key:
    print(json.dumps({"error": "EXA_API_KEY unset — fall back to ralph's web_search"}))
    raise SystemExit(0)
query = "{{ query }}"
try: n = int("{{ num_results }}" or 6)
except Exception: n = 6
payload = json.dumps({"query": query, "numResults": n, "type": "auto",
                      "contents": {"text": {"maxCharacters": 600}}}).encode()
req = urllib.request.Request("https://api.exa.ai/search", data=payload,
    headers={"x-api-key": key, "Content-Type": "application/json"}, method="POST")
try:
    with urllib.request.urlopen(req, timeout=20) as r:
        d = json.load(r)
    out = [{"title": x.get("title"), "url": x.get("url"),
            "snippet": (x.get("text") or "")[:400]} for x in d.get("results", [])]
    print(json.dumps({"query": query, "results": out}, indent=2))
except Exception as e:
    print(json.dumps({"error": str(e)}))
PY
