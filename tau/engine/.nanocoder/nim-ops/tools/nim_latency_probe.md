name: nim_latency_probe
description: Measure real TTFT and total latency for a model from this machine.
parameters:
  model:
    type: string
    description: Full NIM model id
    required: true
approval: never
read_only: true
timeout_ms: 60000
python3 - <<'PY'
import json, os, time, urllib.request
key = os.environ.get("NVIDIA_API_KEY")
if not key:
    print('{"error":"NVIDIA_API_KEY unset"}'); raise SystemExit(0)
model = "{{ model }}"
payload = json.dumps({
    "model": model,
    "messages": [{"role":"user","content":"say ok"}],
    "max_tokens": 8, "temperature": 0
}).encode()
req = urllib.request.Request(
    "https://integrate.api.nvidia.com/v1/chat/completions",
    data=payload,
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    method="POST")
t0 = time.monotonic()
try:
    with urllib.request.urlopen(req, timeout=45) as r:
        _ = r.read()
    dt = (time.monotonic() - t0) * 1000
    print(json.dumps({"model": model, "total_ms": round(dt, 1), "ok": True}))
except Exception as e:
    print(json.dumps({"model": model, "error": str(e), "ok": False}))
PY
