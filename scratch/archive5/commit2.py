#!/usr/bin/env python3
"""Phase 3 (resilient): per-repo archive commits with state persistence,
local blob-SHA computation, and retried ref updates."""
import json, sys, os, base64, time, subprocess, urllib.request, urllib.error
import http.client
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, "/home/hatch/workspace/skills/shared")
import trusted_dns; trusted_dns.patch_socket()
sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import add_surrogate_to_request

OWNER, DEST = "toxicwind", "sovereign-projects"
STAGE = "/home/hatch/workspace/archive_staging"
STATE_F = "/home/hatch/workspace/archive5/commits.json"
manifest = json.load(open("/home/hatch/workspace/archive5/manifest.json"))
recon = json.load(open("/home/hatch/workspace/archive5/recon.json"))
state = json.load(open(STATE_F)) if os.path.exists(STATE_F) else {}

def gh(path, method="GET", data=None, retries=4):
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
        except (urllib.error.HTTPError, http.client.RemoteDisconnected,
                http.client.IncompleteRead, ConnectionError) as e:
            code = getattr(e, "code", type(e).__name__)
            print(f"  retry {attempt+1}/{retries} {method} {path} -> {code}")
            if attempt == retries - 1:
                raise
            time.sleep(3 * (attempt + 1))
    raise AssertionError("unreachable")

def local_blob_sha(stage_path, mode):
    """git blob SHA without API round-trip."""
    if mode == "120000":
        raw = os.readlink(stage_path).encode()
        p = subprocess.run(["git", "hash-object", "-t", "blob", "--stdin"],
                           input=raw, capture_output=True, check=True)
    else:
        p = subprocess.run(["git", "hash-object", stage_path],
                           capture_output=True, text=True, check=True)
    return p.stdout.strip()

def api_create_blob(b64):
    r = gh(f"/repos/{OWNER}/{DEST}/git/blobs", "POST",
           {"content": b64, "encoding": "base64"})
    return r["sha"]

def file_b64(stage_path, mode):
    raw = os.readlink(stage_path).encode() if mode == "120000" else open(stage_path, "rb").read()
    return base64.b64encode(raw).decode()

def current_main():
    return gh(f"/repos/{OWNER}/{DEST}/git/ref/heads/main")["object"]["sha"]

def push_repo(repo, upload):
    """upload=True: POST blobs via API (idempotent). False: trust local SHAs
    (blobs already created in previous run)."""
    info = recon["repos"][repo]
    entries = manifest[repo]["entries"]
    arc = f"from-{repo}"
    print(f"\n=== {repo}: {len(entries)} files (upload={upload}) ===")
    blobmap = {}
    if upload:
        def one(e):
            sp = os.path.join(STAGE, arc, e["path"])
            return e["path"], api_create_blob(file_b64(sp, e["mode"]))
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=16) as ex:
            for path, bsha in ex.map(one, entries):
                blobmap[path] = bsha
        print(f"  blobs uploaded in {time.time()-t0:.1f}s")
    else:
        for e in entries:
            sp = os.path.join(STAGE, arc, e["path"])
            blobmap[e["path"]] = local_blob_sha(sp, e["mode"])
        # spot-check existence of 3 blobs via API
        import random
        for e in random.sample(entries, min(3, len(entries))):
            gh(f"/repos/{OWNER}/{DEST}/git/blobs/{blobmap[e['path']]}")
        print("  blob SHAs computed locally, spot-checks exist OK")

    parent = current_main()
    base_tree = gh(f"/repos/{OWNER}/{DEST}/git/commits/{parent}")["tree"]["sha"]
    tree_entries = [{"path": f"tau/archive/{arc}/{e['path']}", "mode": e["mode"],
                     "type": "blob", "sha": blobmap[e["path"]]} for e in entries]
    tree = gh(f"/repos/{OWNER}/{DEST}/git/trees", "POST",
              {"base_tree": base_tree, "tree": tree_entries})
    msg = (f"Archive unique files from toxicwind/{repo}\n\n"
           f"{len(entries)} files from {repo} main (@{info['head'][:8]}) whose blob SHA "
           f"appears nowhere in sovereign-projects. Consolidation wave 2, 2026-09-14. "
           f"Source repo left untouched.")
    commit = gh(f"/repos/{OWNER}/{DEST}/git/commits", "POST",
                {"message": msg, "tree": tree["sha"], "parents": [parent]})
    new_commit = commit["sha"]
    if current_main() != parent:
        raise RuntimeError(f"main moved during {repo}; aborting ref update")
    gh(f"/repos/{OWNER}/{DEST}/git/ref/heads/main", "PATCH", {"sha": new_commit})
    got = current_main()
    assert got == new_commit, f"ref update failed: {got[:8]} != {new_commit[:8]}"
    print(f"  commit {new_commit[:8]} verified live on main")
    state[repo] = {"commit": new_commit, "tree": tree["sha"], "parent": parent,
                   "files": len(entries)}
    json.dump(state, open(STATE_F, "w"), indent=1)

# sovereign-swap blobs already uploaded in crashed run -> skip re-upload
push_repo("sovereign-swap", upload=False)
push_repo("omp-extensions", upload=True)
push_repo("sovereign-zed", upload=True)
print("\nALL DONE. main =", current_main()[:8])
