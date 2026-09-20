#!/usr/bin/env python3
"""Create .env.example and harden .gitignore in toxicwind/fleet-chat via GitHub API."""
import sys, base64
sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
sys.path.insert(0, "/home/hatch/workspace/env-audit")
from fleetchat_check import gh
import urllib.request, json
from dynamic_credentials import add_surrogate_to_request, read_json_response

def gh_put(path, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request("https://api.github.com" + path, data=data, method="PUT",
        headers={"Accept": "application/vnd.github+json",
                 "Content-Type": "application/json",
                 "User-Agent": "toxicwind-audit/1.0"})
    add_surrogate_to_request(req, "custom.github", allowed_hosts=["api.github.com"])
    with urllib.request.urlopen(req, timeout=30) as resp:
        return read_json_response(resp)

repo = "toxicwind/fleet-chat"

env_example = """# fleet-chat environment variables.
# Copy this file to .env and fill in your values. Every var is optional.
# NEVER commit a real .env — it is gitignored.

# Chat root directory.
# Precedence: --root flag > AGENT_CHAT_ROOT > ~/agent-chat default.
# AGENT_CHAT_ROOT=~/.agent-chat

# Directory for fleet identity key material (signing keys).
# FLEET_KEYS_DIR=~/.fleet-chat/keys
"""

r = gh_put("/repos/%s/contents/.env.example" % repo, {
    "message": "env: add .env.example documenting AGENT_CHAT_ROOT and FLEET_KEYS_DIR",
    "content": base64.b64encode(env_example.encode()).decode(),
    "branch": "main",
})
print("created .env.example:", r["commit"]["sha"][:12])

cur = gh("/repos/%s/contents/.gitignore?ref=main" % repo)
old = base64.b64decode(cur["content"]).decode()
addition = "\n# Environment files (never commit live secrets)\n.env\n.env.local\n!.env.example\n"
new = old.rstrip("\n") + "\n" + addition
r = gh_put("/repos/%s/contents/.gitignore" % repo, {
    "message": "env: gitignore .env and .env.local, keep .env.example tracked",
    "content": base64.b64encode(new.encode()).decode(),
    "sha": cur["sha"],
    "branch": "main",
})
print("updated .gitignore:", r["commit"]["sha"][:12])
