import re, urllib.request, sys

d = open("/home/toxic/.secrets").read()
m = re.search(r'^(?:export\s+)?MISTRAL_API_KEY=["\']?([A-Za-z0-9_\-]{8,})', d, re.M)
key = m.group(1) if m else ""
if not key:
    print("RESULT: no-mistral-key-found")
    sys.exit(0)
req = urllib.request.Request(
    "https://api.mistral.ai/v1/models",
    headers={"Authorization": "Bearer " + key},
)
try:
    r = urllib.request.urlopen(req, timeout=15)
    print("RESULT: mistral-key-alive", r.status)
except Exception as e:
    print("RESULT: mistral-key-dead", str(e)[:100])
