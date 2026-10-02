#!/usr/bin/env python3
"""Create public toxicwind/brand (fork-rebirth of archived Hypr-Agent-Portal).

Flow: create repo under toxicwind org -> verify.
History import + pushes happen from yote via real git.
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dynamic_credentials as dc

ALLOWED = ["*"]
CRED = "custom.github"
REPO = "toxicwind/brand"


def api(method, path, payload=None):
    url = "https://api.github.com" + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "muse-github-skill")
    if data:
        req.add_header("Content-Type", "application/json")
    dc.add_surrogate_to_request(req, CRED, allowed_hosts=ALLOWED)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return dc.read_json_response(resp)


def main():
    try:
        r = api("POST", "/user/repos", {
            "name": "brand",
            "private": False,
            "description": "Native Hyprland plugin + MCP bridge for background agent control — hyper-race verified window focus, input, screenshots. Rebirth of the archived Hypr-Agent-Portal, maintained by the ranch.",
            "auto_init": False,
            "has_issues": True,
            "has_wiki": False,
        })
        print("repo created:", r["full_name"], "private:", r["private"])
    except Exception as e:
        print("create repo:", e)
        r = api("GET", f"/repos/{REPO}")
        print("repo already exists:", r["full_name"], "private:", r["private"])


if __name__ == "__main__":
    main()