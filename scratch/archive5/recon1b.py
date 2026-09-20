#!/usr/bin/env python3
"""Phase 1b: branch uniqueness, orphan size/dir breakdown, secret-like scan."""
import json, sys, urllib.request, urllib.error
from collections import Counter

sys.path.insert(0, "/home/hatch/workspace/skills/shared")
import trusted_dns; trusted_dns.patch_socket()
sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import add_surrogate_to_request

OWNER = "toxicwind"

def gh(path):
    req = urllib.request.Request("https://api.github.com" + path,
        headers={"Accept": "application/vnd.github+json"})
    add_surrogate_to_request(req, "custom.github", allowed_hosts=["api.github.com"])
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, {}

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

recon = json.load(open("/home/hatch/workspace/archive5/recon.json"))
sp_blobs = set(recon["sp_blobs"])

SECRET_HINTS = (".env", "token", "secret", "credential", "passwd", ".pem", ".key",
                "session", ".jsonl", "id_rsa", ".netrc")

for repo in ["sovereign-swap", "sovereign-zed", "omp-extensions"]:
    info = recon["repos"][repo]
    print(f"\n===== {repo} =====")
    orphans = info["orphans"]  # [path, sha, size]
    # size breakdown
    sizes = sorted([sz or 0 for _, _, sz in orphans], reverse=True)
    print(f"orphans={len(orphans)} total_bytes={sum(sizes)} "
          f"top10_bytes={sizes[:10]}")
    # dir breakdown
    dirs = Counter(p.split("/")[0] for p, _, _ in orphans)
    print("top dirs:", dirs.most_common(12))
    # secret-like scan
    sus = [p for p, _, _ in orphans if any(h in p.lower() for h in SECRET_HINTS)]
    print(f"secret-like paths: {sus if sus else 'none'}")
    # big files
    big = [(p, sz) for p, _, sz in orphans if (sz or 0) > 2_000_000]
    print(f"files >2MB: {big if big else 'none'}")

    # branch uniqueness: blobs in branch tree not in main tree and not in sp
    st, maintree = gh(f"/repos/{OWNER}/{repo}/git/trees/{info['head']}?recursive=1")
    main_blobs = {e["sha"] for e in maintree["tree"] if e["type"] == "blob"}
    for br in info["branches"]:
        if br == info["default_branch"]:
            continue
        st, bref = gh(f"/repos/{OWNER}/{repo}/git/ref/heads/{br}")
        if st != 200:
            print(f"  branch {br}: ref lookup failed {st}")
            continue
        bsha = bref["object"]["sha"]
        st, btree = gh(f"/repos/{OWNER}/{repo}/git/trees/{bsha}?recursive=1")
        if st != 200:
            print(f"  branch {br}: tree lookup failed {st}")
            continue
        bblobs = [(e["path"], e["sha"]) for e in btree["tree"] if e["type"] == "blob"]
        uniq = [(p, s) for p, s in bblobs if s not in main_blobs and s not in sp_blobs]
        ahead_note = "SAME-AS-MAIN" if bsha == info["head"] else f"head={bsha[:8]}"
        print(f"  branch {br}: {ahead_note} files={len(bblobs)} "
              f"unique-blobs-not-in-main-or-sp={len(uniq)}")
        for p, s in uniq[:10]:
            print(f"      unique: {p}")
        if len(uniq) > 10:
            print(f"      ... and {len(uniq)-10} more")

    # tag count (full)
    tags = paged(f"/repos/{OWNER}/{repo}/tags")
    print(f"  tags total: {len(tags)}; newest 5: {[t['name'] for t in tags[:5]]}; "
          f"oldest 3: {[t['name'] for t in tags[-3:]]}")
