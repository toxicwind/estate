#!/usr/bin/env python3
"""Rebuild sovereign-router history minus the two kimi token files, then move main.
State is checkpointed to state.json after every API write so a restart can resume."""
import sys, json, os, urllib.request, urllib.error
sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import add_surrogate_to_request, read_response_body, dynamic_credential_entry

REPO = "toxicwind/sovereign-router"
DROP = ["ultimate_extract/kimi_tokens.json", "ultimate_extract/kimi_tokens_full.json"]
UA = "toxicwind-archive-bot/1.0"

def gh(method, path, body=None):
    req = urllib.request.Request("https://api.github.com" + path,
        data=json.dumps(body).encode() if body is not None else None, method=method)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", UA)
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    add_surrogate_to_request(req, "custom.github", allowed_hosts=["api.github.com"])
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = read_response_body(resp)
            return resp.status, (json.loads(raw.decode()) if raw else None)
    except urllib.error.HTTPError as e:
        return e.code, None

def patch_ref(path, body):
    # PATCH via curl_cffi with explicit User-Agent (bare urllib PATCH fails per AGENTS.md)
    from curl_cffi import requests as cr
    entry = dynamic_credential_entry("custom.github")
    placement = entry.get("placement")
    headers = {"Accept": "application/vnd.github+json", "User-Agent": UA,
               "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json"}
    if placement == "bearer_header":
        headers["Authorization"] = "Bearer " + entry["surrogate"]
    elif isinstance(placement, dict) and placement.get("custom_header"):
        headers[placement["custom_header"]] = entry["surrogate"]
    else:
        raise RuntimeError(f"unsupported placement {placement!r}")
    r = cr.patch("https://api.github.com" + path, headers=headers, json=body, timeout=60)
    return r.status_code, (r.json() if r.content else None)

os.chdir(os.path.dirname(os.path.abspath(__file__)))
meta = json.load(open("meta_oldest_first.json"))
state = json.load(open("state.json")) if os.path.exists("state.json") else {"new": {}}

def save():
    json.dump(state, open("state.json", "w"), indent=1)

new_parent = None
for m in meta:
    old = m["sha"]
    if old in state["new"]:
        new_parent = state["new"][old]
        print(f"resume: {old[:8]} already rebuilt as {new_parent[:8]}", flush=True)
        continue
    # 1. new tree minus secret files
    st, t = gh("POST", f"/repos/{REPO}/git/trees",
               {"base_tree": m["tree"],
                "tree": [{"path": p, "mode": "100644", "type": "blob", "sha": None} for p in DROP]})
    assert st == 201, (st, t)
    new_tree = t["sha"]
    # 2. new commit, same metadata
    body = {"message": m["message"], "tree": new_tree,
            "parents": ([new_parent] if new_parent else []),
            "author": {"name": m["author"]["name"], "email": m["author"]["email"], "date": m["author"]["date"]},
            "committer": {"name": m["committer"]["name"], "email": m["committer"]["email"], "date": m["committer"]["date"]}}
    st, c = gh("POST", f"/repos/{REPO}/git/commits", body)
    assert st == 201, (st, c)
    new_parent = c["sha"]
    state["new"][old] = new_parent
    save()
    print(f"rebuilt {old[:8]} -> {new_parent[:8]}", flush=True)

new_head = new_parent
print("new head:", new_head, flush=True)
st, ref = patch_ref(f"/repos/{REPO}/git/refs/heads/main", {"sha": new_head, "force": True})
print("PATCH main:", st, flush=True)
assert st == 200, ref
state["moved"] = True
state["new_head"] = new_head
state["old_head"] = meta[-1]["sha"]
save()
print("DONE", flush=True)
