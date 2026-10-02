#!/usr/bin/env python3
# Dispatch unified-docker.yml with build_cuda=false, build_vulkan=true (vulkan-only retry).
import sys, urllib.request, json
sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import add_surrogate_to_request, read_response_body
HOSTS = ["api.github.com"]
body = json.dumps({"ref": "main", "inputs": {"build_cuda": False, "build_vulkan": True}}).encode()
req = urllib.request.Request(
    "https://api.github.com/repos/toxicwind/herd/actions/workflows/unified-docker.yml/dispatches",
    data=body, method="POST",
    headers={"Accept": "application/vnd.github+json", "Content-Type": "application/json"})
add_surrogate_to_request(req, "custom.github", allowed_hosts=HOSTS)
with urllib.request.urlopen(req, timeout=30) as resp:
    print("dispatch:", resp.status)
