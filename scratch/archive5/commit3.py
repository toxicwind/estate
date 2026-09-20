#!/usr/bin/env python3
"""Phase 3 (final): per-repo archive commits. Objects via urllib API,
ref PATCH via curl_cffi — both with explicit User-Agent (GitHub 403s
UA-less PATCH through this egress path). State saved after each repo."""
import json, sys, os, base64, time, subprocess, urllib.request, urllib.error
import http.client
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, "/home/hatch/workspace/skills/shared")
import trusted_dns; trusted_dns.patch_socket()
sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import dynamic_credential_entry, add_surrogate_to_request
from curl_cffi import requests as cr

OWNER, DEST = "toxicwind", "sovereign-projects"
STAGE = "/home/hatch/workspace/archive_staging"
STATE_F = "/home/hatch/workspace/archive5/commits.json"
UA = "toxicwind-archive-bot/1.0"
manifest = json.load(open("/home/hatch/workspace/archive5/manifest.json"))
recon = json.load(open("/home/hatch/workspace/archive5/recon.json"))
state = json.load(open(STATE_F)) if os.path.exists(STATE_F) else {}
SURR = dynamic_credential_entry("custom.github")["surrogate"]
CH = {"Authorization": f"Bearer {SURR}", "Accept": "application/vnd.github+json",
      "Content-Type": "application/json", "User-Agent": UA}

def gh(path, method="GET", data=None, retries=4):
    body = json.dumps(data).encode() if data is not None else None
    for attempt in range(retries):
        req = urllib.request.Request(
            "https://api.github.com" + path, data=body, method=method,
            headers={"Accept": "application/vnd.github+json",
                     "Content-Type": "application/json", "User-Agent": UA})
        add_surrogate_to_request(req, "custom.github", allowed_hosts=["api.github.com"])
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.load(r)
        except (urllib.error.HTTPError, http.client.RemoteDisconnected,
                http.client.IncompleteRead, ConnectionError) as e:
            print(f"  retry {attempt+1}/{retries} {method} {path} -> {getattr(e,'code',type(e).__name__)}")
            if attempt == retries - 1:
                raise
            time.sleep(3 * (attempt + 1))
    raise AssertionError("unreachable")

def local_blob_sha(stage_path, mode):
    if mode == "120000":
        raw = os.readlink(stage_path).encode()
        p = subprocess.run(["git", "hash-object", "-t", "blob", "--stdin"],
                           input=raw, capture_output=True, check=True)
    else:
        p = subprocess.run(["git", "hash-object", stage_path],
                           capture_output=True, text=True, check=True)
    return p.stdout.strip()

def api_create_blob(b64):
    return gh(f"/repos/{OWNER}/{DEST}/git/blobs", "POST",
              {"content": b64, "encoding": "base64"})["sha"]

def file_b64(stage_path, mode):
    raw = os.readlink(stage_path).encode() if mode == "120000" else open(stage_path, "rb").read()
    return base64.b64encode(raw).decode()

def current_main():
    return gh(f"/repos/{OWNER}/{DEST}/git/ref/heads/main")["object"]["sha"]

def patch_main(new_sha, expect_parent):
    if current_main() != expect_parent:
        raise RuntimeError("main moved unexpectedly; aborting")
    for attempt in range(4):
        r = cr.patch(
            f"https://api.github.com/repos/{OWNER}/{DEST}/git/refs/heads/main",
            headers=CH, json={"sha": new_sha}, timeout=60)
        if r.status_code == 200:
            break
        print(f"  PATCH retry {attempt+1}/4 -> {r.status_code} {r.text[:120]}")
        time.sleep(3 * (attempt + 1))
    else:
        raise RuntimeError(f"PATCH failed: {r.status_code} {r.text[:200]}")
    got = current_main()
    assert got == new_sha, f"ref mismatch {got[:8]} != {new_sha[:8]}"
    print(f"  main -> {new_sha[:8]} verified")

def push_repo(repo, upload):
    if repo in state:
        print(f"=== {repo}: already done ({state[repo]['commit'][:8]}), skipping ===")
        return
    info = recon["repos"][repo]
    entries = manifest[repo]["entries"]
    arc = f"from-{repo}"
    print(f"\n=== {repo}: {len(entries)} files (upload={upload}) ===")
    t0 = time.time()
    if upload:
        def one(e):
            sp = os.path.join(STAGE, arc, e["path"])
            return e["path"], api_create_blob(file_b64(sp, e["mode"]))
        blobmap = {}
        with ThreadPoolExecutor(max_workers=16) as ex:
            for path, bsha in ex.map(one, entries):
                blobmap[path] = bsha
    else:
        blobmap = {e["path"]: local_blob_sha(os.path.join(STAGE, arc, e["path"]), e["mode"])
                   for e in entries}
        for e in entries[:3]:
            gh(f"/repos/{OWNER}/{DEST}/git/blobs/{blobmap[e['path']]}")  # existence check
    print(f"  blobs ready in {time.time()-t0:.1f}s")
    parent = current_main()
    base_tree = gh(f"/repos/{OWNER}/{DEST}/git/commits/{parent}")["tree"]["sha"]
    tree = gh(f"/repos/{OWNER}/{DEST}/git/trees", "POST", {
        "base_tree": base_tree,
        "tree": [{"path": f"tau/archive/{arc}/{e['path']}", "mode": e["mode"],
                  "type": "blob", "sha": blobmap[e["path"]]} for e in entries]})
    msg = (f"Archive unique files from toxicwind/{repo}\n\n"
           f"{len(entries)} files from {repo} main (@{info['head'][:8]}) whose blob SHA "
           f"appears nowhere in sovereign-projects. Consolidation wave 2, 2026-09-14. "
           f"Source repo left untouched.")
    commit = gh(f"/repos/{OWNER}/{DEST}/git/commits", "POST",
                {"message": msg, "tree": tree["sha"], "parents": [parent]})
    new_sha = commit["sha"]
    print(f"  commit object {new_sha[:8]} created")
    patch_main(new_sha, parent)
    state[repo] = {"commit": new_sha, "tree": tree["sha"], "parent": parent,
                   "files": len(entries)}
    json.dump(state, open(STATE_F, "w"), indent=1)

push_repo("sovereign-swap", upload=False)   # blobs already exist from run 1
push_repo("omp-extensions", upload=True)
push_repo("sovereign-zed", upload=True)
print("\nALL ARCHIVE COMMITS DONE. main =", current_main()[:8])
