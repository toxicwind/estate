#!/usr/bin/env python3
"""Discover all models reachable by the NVIDIA NIM API key and report which are 'free' / allowed."""

import json
import os
import sys
import urllib.request

BASE = "https://integrate.api.nvidia.com/v1"
KEY = os.environ.get("NVIDIA_API_KEY") or os.environ.get("NVIDIA_NIM_API_KEY")
if not KEY:
    print("ERROR: set NVIDIA_API_KEY", file=sys.stderr)
    sys.exit(1)

req = urllib.request.Request(
    f"{BASE}/models", headers={"Authorization": f"Bearer {KEY}"}
)
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
except Exception as e:
    print(f"ERROR fetching /models: {e}", file=sys.stderr)
    sys.exit(1)

models = data.get("data", [])
print(f"TOTAL models returned: {len(models)}")
print("=" * 80)
# Print id + any useful metadata
for m in models:
    mid = m.get("id")
    # NVIDIA sometimes nests capabilities; just dump keys we care about
    owned = m.get("owned_by", "")
    root = m.get("root", "")
    print(f"{mid}  | owned_by={owned} root={root}")
