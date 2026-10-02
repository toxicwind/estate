#!/usr/bin/env python3
"""Create private toxicwind/awrawr-mcp and push the initial root commit.

Flow: create repo -> seed README via Contents API (empty repos 409 on git
refs) -> blobs -> tree -> root commit (no parents) -> force-move main to it
(documented empty-repo pattern) -> verify ref.
"""
import base64
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dynamic_credentials as dc

ALLOWED = ["*"]
CRED = "custom.github"
REPO = "toxicwind/awrawr-mcp"


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
    # NOTE: one-shot script — toxicwind/awrawr-mcp already exists; these paths
    # are only used if the script is re-run. Staging is in durable workspace
    # scratch, never /tmp (tmpfs janitor — Chris 2026-09-30).
    scratch = os.path.join(os.path.expanduser("~"), "workspace", ".tmpdir", "forgefire")
    files = {
        "awrawr_mcp.py": f"{scratch}/awrawr_mcp.py",
        "README.md": f"{scratch}/README.md",
        ".gitignore": f"{scratch}/.gitignore",
    }
    # 1. create the private repo
    try:
        r = api("POST", "/user/repos", {
            "name": "awrawr-mcp",
            "private": True,
            "description": "Hardened MCP exec bridge for yote (single-file service, :25198)",
            "auto_init": False,
        })
        print("repo created:", r["full_name"], "private:", r["private"])
    except Exception as e:
        print("create repo:", e)
        r = api("GET", f"/repos/{REPO}")
        print("repo already exists:", r["full_name"], "private:", r["private"])

    # 2. seed README via Contents API so the ref exists (409 workaround)
    with open(files["README.md"], "rb") as f:
        seed_b64 = base64.b64encode(f.read()).decode()
    try:
        s = api("PUT", f"/repos/{REPO}/contents/README.md",
                {"message": "seed", "content": seed_b64, "branch": "main"})
        print("seed commit:", s["commit"]["sha"][:8])
    except Exception as e:
        print("seed:", e)

    # 3. blobs -> tree -> root commit
    tree_entries = []
    for path, local in files.items():
        with open(local, "rb") as f:
            content = base64.b64encode(f.read()).decode()
        blob = api("POST", f"/repos/{REPO}/git/blobs",
                   {"content": content, "encoding": "base64"})
        mode = "100755" if path == "awrawr_mcp.py" else "100644"
        tree_entries.append({"path": path, "mode": mode,
                             "type": "blob", "sha": blob["sha"]})
    tree = api("POST", f"/repos/{REPO}/git/trees", {"tree": tree_entries})
    ident = {"name": "forgefire", "email": "forgefire@local"}
    commit = api("POST", f"/repos/{REPO}/git/commits", {
        "message": ("awrawr-mcp: initial commit\n\n"
                    "Single-file hardened MCP exec bridge (:25198), 29 tools.\n"
                    "Extracted from toxicwind/sovereign-projects "
                    "projects/bridge/yote/awrawr_mcp.py @ 39d11426c5 "
                    "(post-audit fixes)."),
        "tree": tree["sha"], "parents": [],
        "author": ident, "committer": ident})
    print("root commit:", commit["sha"])

    # 4. force-move main to the root commit, then verify
    api("PATCH", f"/repos/{REPO}/git/refs/heads/main",
        {"sha": commit["sha"], "force": True})
    ref = api("GET", f"/repos/{REPO}/git/refs/heads/main")
    final = ref["object"]["sha"]
    assert final == commit["sha"], f"ref mismatch: {final} != {commit['sha']}"
    print("main:", final)
    print("url: https://github.com/" + REPO)


if __name__ == "__main__":
    main()