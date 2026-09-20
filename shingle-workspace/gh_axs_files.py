#!/usr/bin/env python3
"""Fetch the interesting AXS-related files found via GitHub code search."""
import base64
import json
import os
import sys
import urllib.request

sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import add_surrogate_to_request, read_response_body

HOSTS = ["api.github.com"]

FILES = [
    ("idknox/soundlocale", "app/services/axs.rb"),
    ("idknox/soundlocale-api", "app/services/axs_service.rb"),
    ("SERORN/axs-mobile-2-", "src/config/env.ts"),
]


def gh_get(url):
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "shingle-gh-fetch/1.0")
    add_surrogate_to_request(req, "custom.github", allowed_hosts=HOSTS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(read_response_body(resp).decode("utf-8"))


for repo, path in FILES:
    print("=" * 70)
    print(repo, path)
    try:
        data = gh_get("https://api.github.com/repos/%s/contents/%s" % (repo, path))
        content = base64.b64decode(data["content"]).decode("utf-8", "replace")
        print(content[:6000])
    except Exception as e:
        print("ERR:", str(e)[:300])
