#!/usr/bin/env python3
"""Phase 1: read-only recon for 5 repos + current sovereign-projects tree."""
import json, sys, urllib.request, urllib.error

sys.path.insert(0, "/home/hatch/workspace/skills/shared")
import trusted_dns; trusted_dns.patch_socket()
sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import add_surrogate_to_request

OWNER = "toxicwind"
REPOS = ["sovereign-scripts", "sovereign-skills", "sovereign-swap", "sovereign-zed", "omp-extensions"]

def gh(path, method="GET", data=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request("https://api.github.com" + path,
        data=body, method=method,
        headers={"Accept": "application/vnd.github+json",
                 "Content-Type": "application/json"})
    add_surrogate_to_request(req, "custom.github", allowed_hosts=["api.github.com"])
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {"_err": e.code}

def paged(path):
    out, page = [], 1
    while True:
        st, batch = gh(f"{path}?per_page=100&page={page}")
        if st != 200 or not isinstance(batch, list) or not batch:
            break
        out.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return out

result = {"repos": {}}

# sovereign-projects current tree -> blob sha set
st, sp = gh("/repos/toxicwind/sovereign-projects")
sp_default = sp["default_branch"]
st, spref = gh(f"/repos/toxicwind/sovereign-projects/git/ref/heads/{sp_default}")
sp_head = spref["object"]["sha"]
st, sptree = gh(f"/repos/toxicwind/sovereign-projects/git/trees/{sp_head}?recursive=1")
assert st == 200, sptree
print(f"sovereign-projects: default={sp_default} head={sp_head[:8]} "
      f"tree_entries={len(sptree['tree'])} truncated={sptree.get('truncated')}")
sp_blobs = {e["sha"] for e in sptree["tree"] if e["type"] == "blob"}
print(f"sovereign-projects blob count: {len(sp_blobs)}")
result["sp_head"] = sp_head
result["sp_blobs"] = sorted(sp_blobs)

for repo in REPOS:
    info = {}
    st, meta = gh(f"/repos/{OWNER}/{repo}")
    assert st == 200, (repo, st, meta)
    info["private"] = meta["private"]
    info["default_branch"] = meta["default_branch"]
    info["pushed_at"] = meta["pushed_at"]
    branches = paged(f"/repos/{OWNER}/{repo}/branches")
    info["branches"] = [b["name"] for b in branches]
    tags = paged(f"/repos/{OWNER}/{repo}/tags")
    info["tags"] = [t["name"] for t in tags]
    st, ref = gh(f"/repos/{OWNER}/{repo}/git/ref/heads/{meta['default_branch']}")
    head = ref["object"]["sha"]
    info["head"] = head
    st, tree = gh(f"/repos/{OWNER}/{repo}/git/trees/{head}?recursive=1")
    assert st == 200, (repo, st)
    entries = tree["tree"]
    info["truncated"] = tree.get("truncated")
    blobs = [(e["path"], e["sha"], e.get("size", 0)) for e in entries if e["type"] == "blob"]
    info["file_count"] = len(blobs)
    orphans = [(p, s, sz) for (p, s, sz) in blobs if s not in sp_blobs]
    info["orphans"] = orphans
    info["orphan_count"] = len(orphans)
    info["total_blob_bytes"] = sum(sz or 0 for _, _, sz in orphans)
    result["repos"][repo] = info
    print(f"{repo}: private={info['private']} default={info['default_branch']} "
          f"branches={info['branches']} tags={info['tags'][:8]}{'...' if len(info['tags'])>8 else ''} "
          f"files={info['file_count']} orphans={info['orphan_count']} "
          f"orphan_bytes={info['total_blob_bytes']} truncated={info['truncated']}")

with open("/home/hatch/workspace/archive5/recon.json", "w") as f:
    json.dump(result, f, indent=1)
print("saved recon.json")
