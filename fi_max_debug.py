#!/usr/bin/env python3
import os, sys, json, time
from curl_cffi import requests

KEY = os.environ.get("FI_KEY") or os.environ.get("FREEINFERENCE_API_KEY")
if not KEY:
    sys.exit("[!] Set FI_KEY: export FI_KEY='hyi-...'")

def debug_response(title, r, ms):
    print(f"\n{'='*30} {title} {'='*30}")
    print(f"HTTP Status: {r.status_code}")
    print(f"Latency:     {ms:.2f} ms")
    print(f"URL:         {r.url}")
    print("--- RESPONSE HEADERS ---")
    for k, v in r.headers.items():
        print(f"  {k}: {v}")
    print("--- RAW BODY ---")
    try:
        print(json.dumps(r.json(), indent=2))
    except Exception:
        print(r.text)
    print("=" * (62 + len(title)))

# 1. Local Thresher (:25127) Probe
t0 = time.perf_counter()
try:
    r_local = requests.get("http://127.0.0.1:25127/health", timeout=3)
    debug_response("LOCAL GATEHOUSE :25127/health", r_local, (time.perf_counter() - t0) * 1000)
except Exception as e:
    print(f"\n[!] Local Thresher Exception: {e}")

# 2. Remote FreeInference API Call (Estate / Thresher Context)
url_remote = "https://freeinference.org/v1/chat/completions"
headers_remote = {
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

payload_remote = {
    "model": "qwen3.6-35b",
    "messages": [
        {
            "role": "system",
            "content": "You are gatehouse-guard in estate/gatehouse managing mcpproxy-go and toolcall-llm."
        },
        {
            "role": "user",
            "content": "Confirm you received gatehouse context. Reply in 10 words."
        }
    ],
    "max_tokens": 999999,
    "temperature": 0.0
}

print(f"\n>>> SENDING TO {url_remote} (curl_cffi Chrome TLS)")
print("--- REQUEST PAYLOAD ---")
print(json.dumps(payload_remote, indent=2))

t1 = time.perf_counter()
r_remote = requests.post(
    url_remote,
    headers=headers_remote,
    json=payload_remote,
    impersonate="chrome",
    timeout=60
)
debug_response("REMOTE FREEINFERENCE CHAT", r_remote, (time.perf_counter() - t1) * 1000)
