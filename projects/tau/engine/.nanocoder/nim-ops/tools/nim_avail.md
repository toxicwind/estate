name: nim_avail
description: List models available on this account's NIM key.
approval: never
read_only: true
timeout_ms: 30000
python3 - <<'PY'
import json, os, urllib.request
key = os.environ.get("NVIDIA_API_KEY")
if not key:
    print('{"error":"NVIDIA_API_KEY unset"}'); raise SystemExit(0)
req = urllib.request.Request("https://integrate.api.nvidia.com/v1/models",
                             headers={"Authorization": f"Bearer {key}"})
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        d = json.load(r)
    ids = [m["id"] for m in d.get("data", [])]
    print(json.dumps({"count": len(ids), "models": ids}, indent=2))
except Exception as e:
    print(json.dumps({"error": str(e)}))
PY
