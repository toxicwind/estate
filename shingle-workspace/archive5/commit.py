#!/usr/bin/env python3
"""Phase 3: push one archive commit per repo via GitHub git API."""
import json, sys, os, base64, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, "/home/hatch/workspace/skills/shared")
import trusted_dns; trusted_dns.patch_socket()
sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import add_surrogate_to_request

OWNER, DEST = "toxicwind", "sovereign-projects"
STAGE = "/home/hatch/workspace/archive_staging"
manifest = json.load(open("/home/hatch/workspace/archive5/manifest.json"))
recon = json.load(open("/home/hatch/workspace/archive5/recon.json"))

def gh(path, method="GET", data=None, retries=3):
    body = json.dumps(data).encode() if data is not None else None
    for attempt in range(retries):
        req = urllib.request.Request(
            "https://api.github.com" + path, data=body, method=method,
            headers={"Accept": "application/vnd.github+json",
                     "Content-Type": "application/json"})
        add_surrogate_to_request(req, "custom.github", allowed_hosts=["api.github.com"])
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            err = e.read().decode()[:300]
            if attempt == retries - 1:
                raise RuntimeError(f"{method} {path} -> {e.code}: {err}")
            time.sleep(2 * (attempt + 1))
    raise AssertionError("unreachable")

def create_blob(b64):
    r = gh(f"/repos/{OWNER}/{DEST}/git/blobs", "POST",
           {"content": b64, "encoding": "base64"})
    return r["sha"]

def file_b64(stage_path, mode):
    if mode == "120000":
        raw = os.readlink(stage_path).encode()
    else:
        with open(stage_path, "rb") as f:
            raw = f.read()
    return base64.b64encode(raw).decode()

# resolve base tree = tree sha of current main head
ref = gh(f"/repos/{OWNER}/{DEST}/git/ref/heads/main")
head_sha = ref["object"]["sha"]
assert head_sha == recon["sp_head"], f"main moved! {head_sha} vs {recon['sp_head']}"
commit_obj = gh(f"/repos/{OWNER}/{DEST}/git/commits/{head_sha}")
base_tree = commit_obj["tree"]["sha"]
parent = head_sha
print(f"starting from main={parent[:8]} tree={base_tree[:8]}")

results = {}
REPO_ORDER = ["sovereign-swap", "omp-extensions", "sovereign-zed"]  # small first
for repo in REPO_ORDER:
    info = recon["repos"][repo]
    entries = manifest[repo]["entries"]
    arc = f"from-{repo}"
    print(f"\n--- {repo}: creating {len(entries)} blobs ---")
    t0 = time.time()
    blobmap = {}
    def one(e):
        sp = os.path.join(STAGE, arc, e["path"])
        return e["path"], create_blob(file_b64(sp, e["mode"]))
    with ThreadPoolExecutor(max_workers=16) as ex:
        for path, bsha in ex.map(one, entries):
            blobmap[path] = bsha
    print(f"blobs done in {time.time()-t0:.1f}s")
    tree_entries = [{"path": f"tau/archive/{arc}/{e['path']}", "mode": e["mode"],
                     "type": "blob", "sha": blobmap[e["path"]]} for e in entries]
    tree = gh(f"/repos/{OWNER}/{DEST}/git/trees", "POST",
              {"base_tree": base_tree, "tree": tree_entries})
    new_tree = tree["sha"]
    msg = (f"Archive unique files from toxicwind/{repo}\n\n"
           f"{len(entries)} files from {repo} main (@{info['head'][:8]}) whose blob SHA "
           f"appears nowhere in sovereign-projects. Consolidation wave 2, 2026-09-14. "
           f"Source repo left untouched.")
    commit = gh(f"/repos/{OWNER}/{DEST}/git/commits", "POST",
                {"message": msg, "tree": new_tree, "parents": [parent]})
    new_commit = commit["sha"]
    # fast-forward guard
    ref2 = gh(f"/repos/{OWNER}/{DEST}/git/ref/heads/main")
    if ref2["object"]["sha"] != parent:
        raise RuntimeError(f"main moved during {repo} push; aborting before ref update")
    gh(f"/repos/{OWNER}/{DEST}/git/ref/heads/main", "PATCH", {"sha": new_commit})
    print(f"{repo}: commit {new_commit[:8]} live on main")
    results[repo] = {"commit": new_commit, "tree": new_tree,
                     "parent": parent, "files": len(entries)}
    parent, base_tree = new_commit, new_tree

json.dump(results, open("/home/hatch/workspace/archive5/commits.json", "w"), indent=1)
print("\nfinal main:", parent[:8])
print("commits.json saved")
