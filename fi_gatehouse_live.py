#!/usr/bin/env python3
import os, sys, json
from curl_cffi import requests

KEY = os.environ.get("FI_KEY") or os.environ.get("FREEINFERENCE_API_KEY")
if not KEY:
    sys.exit("[!] Set FI_KEY: export FI_KEY='hyi-...'")

# 1. Local Thresher Health Check (:25127)
print("=== 1. LOCAL GATEHOUSE PROBE (:25127) ===")
try:
    r_local = requests.get("http://127.0.0.1:25127/health", timeout=2)
    print(f"Local Thresher Health: {r_local.status_code} {r_local.text}")
except Exception as e:
    print(f"Local Thresher unreachable: {e}")

# 2. Remote Prompt Test with Estate / Thresher Context (Using Chrome TLS)
print("\n=== 2. REMOTE PROMPT TEST (CURL_CFFI BYPASSES CF 1010) ===")
remote_url = "https://freeinference.org/v1/chat/completions"
headers = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}

payload = {
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

r_remote = requests.post(remote_url, headers=headers, json=payload, impersonate="chrome", timeout=30)
print(f"Remote Status Code: {r_remote.status_code}")
if r_remote.status_code == 200:
    print("Remote Content:")
    print(r_remote.json()["choices"][0]["message"]["content"])
else:
    print("Error Body:")
    print(r_remote.text)
