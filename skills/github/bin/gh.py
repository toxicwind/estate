#!/usr/bin/env python3
"""Minimal CLI for the GitHub REST API using the stored custom.github credential.

Usage:
  gh.py search-repos <query> [--per-page N]
  gh.py repo <owner/repo>
  gh.py contents <owner/repo> [path]
  gh.py get <path> [--params key=value ...]
  gh.py create-gist <file> [--public] [--description TEXT] [--filename NAME]

Allowed hosts: * (operator chose all-hosts). The credential value is
never visible; authd substitutes it for the surrogate at egress time.
"""
import json
import os
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dynamic_credentials as dc

ALLOWED = ["*"]  # operator choice: all hosts allowed for this credential
CRED = "custom.github"


def api_get(path, params=None):
    url = "https://api.github.com" + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "muse-github-skill")
    dc.add_surrogate_to_request(req, CRED, allowed_hosts=ALLOWED)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return dc.read_json_response(resp)


def api_post(path, payload):
    url = "https://api.github.com" + path
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "muse-github-skill")
    req.add_header("Content-Type", "application/json")
    dc.add_surrogate_to_request(req, CRED, allowed_hosts=ALLOWED)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return dc.read_json_response(resp)


def api_patch(path, payload):
    url = "https://api.github.com" + path
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="PATCH")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "muse-github-skill")
    req.add_header("Content-Type", "application/json")
    dc.add_surrogate_to_request(req, CRED, allowed_hosts=ALLOWED)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return dc.read_json_response(resp)


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]
    try:
        if cmd == "search-repos":
            if not rest:
                raise ValueError("query required")
            per_page = 10
            if "--per-page" in rest:
                i = rest.index("--per-page")
                per_page = int(rest[i + 1])
                rest = rest[:i] + rest[i + 2:]
            q = " ".join(rest)
            data = api_get("/search/repositories", {"q": q, "per_page": per_page})
            out = []
            for r in data.get("items", []):
                out.append({
                    "full_name": r["full_name"],
                    "description": r.get("description"),
                    "stars": r.get("stargazers_count"),
                    "url": r.get("html_url"),
                    "default_branch": r.get("default_branch"),
                })
            print(json.dumps({"total": data.get("total_count"), "items": out}, indent=2))
        elif cmd == "repo":
            print(json.dumps(api_get("/repos/" + rest[0]), indent=2))
        elif cmd == "contents":
            owner_repo = rest[0]
            path = rest[1] if len(rest) > 1 else ""
            print(json.dumps(api_get("/repos/" + owner_repo + "/contents/" + path), indent=2))
        elif cmd == "get":
            params = {}
            path = rest[0]
            extra = rest[1:]
            i = 0
            while i < len(extra):
                if extra[i] == "--params" and i + 1 < len(extra):
                    k, _, v = extra[i + 1].partition("=")
                    params[k] = v
                    i += 2
                else:
                    i += 1
            print(json.dumps(api_get(path, params or None), indent=2))
        elif cmd == "create-gist":
            if not rest:
                raise ValueError("file required")
            src = rest[0]
            public = "--public" in rest
            desc = "gist"
            fname = os.path.basename(src)
            args = [a for a in rest[1:] if a != "--public"]
            i = 0
            while i < len(args):
                if args[i] == "--description" and i + 1 < len(args):
                    desc = args[i + 1]
                    i += 2
                elif args[i] == "--filename" and i + 1 < len(args):
                    fname = args[i + 1]
                    i += 2
                else:
                    i += 1
            with open(src, "r", encoding="utf-8") as f:
                content = f.read()
            data = api_post("/gists", {
                "description": desc,
                "public": public,
                "files": {fname: {"content": content}},
            })
            print(json.dumps({"id": data.get("id"),
                              "url": data.get("html_url")}, indent=2))
        else:
            raise ValueError(f"unknown command: {cmd}")
    except Exception as e:  # noqa: BLE001 - report plainly
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))