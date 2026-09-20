import sys
sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import dynamic_credential_entry

COMMIT = "23c82cb5c4128986801f5f93bb4c7ce1ff262cce"
UA = "toxicwind-readme-fix/1.0"

entry = dynamic_credential_entry("custom.github")
surr = str(entry["surrogate"]).strip()
placement = entry.get("placement")
auth = {}
if placement == "bearer_header":
    auth["Authorization"] = f"Bearer {surr}"
elif isinstance(placement, dict) and isinstance(placement.get("custom_header"), str):
    auth[placement["custom_header"]] = surr
else:
    raise SystemExit(f"unsupported placement: {placement!r}")

from curl_cffi import requests as creq
r = creq.patch(
    "https://api.github.com/repos/toxicwind/herd/git/refs/heads/main",
    headers={"Accept": "application/vnd.github+json", "User-Agent": UA,
             "Content-Type": "application/json", **auth},
    json={"sha": COMMIT},
    impersonate="chrome",
    timeout=30,
)
print("patch status:", r.status_code)
if r.status_code not in (200, 201):
    print(r.text[:500]); sys.exit(1)

import urllib.request, json
from dynamic_credentials import add_surrogate_to_request, read_json_response
req = urllib.request.Request(
    "https://api.github.com/repos/toxicwind/herd/git/ref/heads/main",
    headers={"Accept": "application/vnd.github+json", "User-Agent": UA})
add_surrogate_to_request(req, "custom.github", allowed_hosts=["api.github.com"])
ref = read_json_response(urllib.request.urlopen(req, timeout=30))
print("main now:", ref["object"]["sha"][:8])
assert ref["object"]["sha"] == COMMIT, "ref did not move!"
print("PUSH OK", COMMIT[:8])
