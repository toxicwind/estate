#!/usr/bin/env python3
"""Create a branch ref at a known sha via the GitHub git-database API."""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dynamic_credentials as dc

repo, branch, sha = sys.argv[1], sys.argv[2], sys.argv[3]
url = f"https://api.github.com/repos/{repo}/git/refs"
payload = {"ref": f"refs/heads/{branch}", "sha": sha}
req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST")
req.add_header("Accept", "application/vnd.github+json")
req.add_header("X-GitHub-Api-Version", "2022-11-28")
req.add_header("User-Agent", "muse-github-skill")
req.add_header("Content-Type", "application/json")
dc.add_surrogate_to_request(req, "custom.github", allowed_hosts=["*"])
with urllib.request.urlopen(req, timeout=60) as resp:
    out = json.load(resp)
print(out["ref"], "->", out["object"]["sha"])