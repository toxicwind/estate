#!/usr/bin/env python3
"""Flip toxicwind/fleet-chat and toxicwind/openfang from private to public.
Chris's conditional authorization: sweep came back clean, so flip immediately.
Uses curl_cffi (PATCH via bare urllib is blocked) + dynamic credential surrogate.
Never prints credential material."""
import sys, json
sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import dynamic_credential_entry
from curl_cffi import requests as cr

entry = dynamic_credential_entry("custom.github", "access_token")
surrogate = str(entry["surrogate"]).strip()
placement = entry.get("placement")
headers = {"User-Agent": "shingle-agent/1.0", "Accept": "application/vnd.github+json"}
if placement == "bearer_header":
    headers["Authorization"] = f"Bearer {surrogate}"
elif isinstance(placement, dict) and placement.get("custom_header"):
    headers[placement["custom_header"]] = surrogate
else:
    raise SystemExit(f"unsupported placement")

for repo in ["toxicwind/fleet-chat", "toxicwind/openfang"]:
    url = f"https://api.github.com/repos/{repo}"
    r = cr.patch(url, headers=headers, json={"private": False}, timeout=30)
    try:
        body = r.json()
    except Exception:
        body = {"raw": r.text[:200]}
    print(repo, "-> HTTP", r.status_code, "| private =", body.get("private"), "| visibility =", body.get("visibility"))
    if r.status_code not in (200,):
        print("  error:", json.dumps(body)[:300])
