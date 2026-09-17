#!/usr/bin/env python3
"""Raw SSE capture for one Ling call. Prints byte count, elapsed, and the raw
stream head so we can see reasoning deltas / finish_reason / usage. No key
material is printed."""
import json
import re
import time
import urllib.request

vals = {}
with open("/home/toxic/.secrets") as f:
    for line in f:
        m = re.match(r"\s*(?:export\s+)?(OPENROUTER[A-Za-z_]*)\s*=\s*(.+?)\s*$", line)
        if m:
            vals[m.group(1)] = m.group(2).strip().strip('"').strip("'")
key = vals["OPENROUTER_API_KEY"]

body = json.dumps(
    {
        "model": "inclusionai/ling-3.0-flash-fin:free",
        "messages": [
            {"role": "user", "content": "What is 17*23? Reply with just the number."}
        ],
        "max_tokens": 64,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
).encode()
req = urllib.request.Request(
    "https://openrouter.ai/api/v1/chat/completions",
    data=body,
    headers={
        "Authorization": "Bearer " + key,
        "Content-Type": "application/json",
        "HTTP-Referer": "https://awrawr-pc/",
        "X-Title": "ling-raw",
    },
)
chunks = []
t0 = time.time()
try:
    with urllib.request.urlopen(req, timeout=90) as r:
        for chunk in r:
            chunks.append(chunk.decode("utf-8", "replace"))
except Exception as e:  # noqa: BLE001
    print("TRANSPORT_ERROR", type(e).__name__, str(e)[:200])
raw = "".join(chunks)
print("BYTES", len(raw))
print("SECONDS", round(time.time() - t0, 2))
print("---- RAW HEAD (first 3000 chars) ----")
print(raw[:3000])
print("---- TAIL (last 800 chars) ----")
print(raw[-800:])
