#!/usr/bin/env python3
"""Check toxicwind/fleet-chat for .env.example presence and any tracked .env-ish files."""
import sys, json
sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import add_surrogate_to_request, read_json_response
import urllib.request

def gh(path):
    req = urllib.request.Request("https://api.github.com" + path,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "toxicwind-audit/1.0"})
    add_surrogate_to_request(req, "custom.github",
        allowed_hosts=["api.github.com"])
    with urllib.request.urlopen(req, timeout=30) as resp:
        return read_json_response(resp)

repo = "toxicwind/fleet-chat"
# get default branch + full file tree
info = gh("/repos/%s" % repo)
branch = info["default_branch"]
tree = gh("/repos/%s/git/trees/%s?recursive=1" % (repo, branch))
env_files = [t["path"] for t in tree["tree"]
             if ".env" in t["path"].lower() or "kimi_tokens" in t["path"].lower()]
print("default_branch:", branch)
print("total blobs:", tree.get("truncated", False) and "TRUNCATED" or len(tree["tree"]))
print("env-ish tracked files:")
for f in env_files:
    print("  ", f)
# fetch .env.example content if present
if ".env.example" in env_files:
    blob = gh("/repos/%s/contents/.env.example?ref=%s" % (repo, branch))
    import base64
    content = base64.b64decode(blob["content"]).decode("utf-8", "replace")
    print("--- .env.example (%d lines) ---" % len(content.splitlines()))
    print(content[:2000])
