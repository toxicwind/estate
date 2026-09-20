#!/usr/bin/env python3
"""Phase 1: download all merge sources into $MERGE_STAGE + manifest."""
import sys, os, json, base64, tarfile, io
sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import dynamic_credential_entry
from curl_cffi import requests as crequests
from concurrent.futures import ThreadPoolExecutor

entry = dynamic_credential_entry("custom.github")
SUR = entry["surrogate"]
H = {
    "Accept": "application/vnd.github+json",
    "Authorization": "Bearer %s" % SUR,
    "User-Agent": "toxicwind-archive-bot/1.0",
    "X-GitHub-Api-Version": "2022-11-28",
}
STAGE = os.environ.get("MERGE_STAGE", "/tmp/merge")
os.makedirs(STAGE, exist_ok=True)
manifest = {"sources": {}}

def tree_recursive(repo, ref):
    r = crequests.get(f"https://api.github.com/repos/toxicwind/{repo}/git/trees/{ref}",
                      headers=H, params={"recursive": "1"}, timeout=120)
    r.raise_for_status()
    return r.json()["tree"]

def get_blob(repo, sha):
    r = crequests.get(f"https://api.github.com/repos/toxicwind/{repo}/git/blobs/{sha}",
                      headers=H, timeout=60)
    r.raise_for_status()
    d = r.json()
    assert d["encoding"] == "base64"
    return base64.b64decode(d["content"])

def dl_tarball(repo, branch, dest):
    os.makedirs(dest, exist_ok=True)
    r = crequests.get(f"https://api.github.com/repos/toxicwind/{repo}/tarball/{branch}",
                      headers={"Authorization": f"Bearer {SUR}", "User-Agent": "toxicwind-archive-bot/1.0"},
                      timeout=300)
    r.raise_for_status()
    tf = tarfile.open(fileobj=io.BytesIO(r.content))
    tf.extractall(dest)
    kids = os.listdir(dest)
    print(f"  tarball {repo}: {len(r.content)//1024}KB -> {kids}", flush=True)

# ---- tarballs for small repos ----
for repo, branch in [("kimi-skills", "main"), ("moonbox-skills-deploy", "master"),
                     ("claude-forge", "main"), ("kimi-internal-toolkit", "main"),
                     ("nvidia-swarm-lens", "main")]:
    print("tarball:", repo, flush=True)
    dl_tarball(repo, branch, f"{STAGE}/tar/{repo}")
manifest["sources"]["tarballs"] = ["kimi-skills", "moonbox-skills-deploy", "claude-forge",
                                   "kimi-internal-toolkit", "nvidia-swarm-lens"]

# ---- July catalog: tree of commit 43c286cea604 in gear ----
print("july catalog...", flush=True)
jtree = tree_recursive("gear", "43c286cea604")
jblobs = [(x["path"], x["sha"]) for x in jtree if x["type"] == "blob"]
def w_july(item):
    path, sha = item
    data = get_blob("gear", sha)
    fp = os.path.join(STAGE, "july", path)
    os.makedirs(os.path.join(STAGE, "july", os.path.dirname(path)), exist_ok=True)
    open(fp, "wb").write(data)
    return path
with ThreadPoolExecutor(max_workers=12) as ex:
    done = list(ex.map(w_july, jblobs))
print(f"  july: {len(done)} files", flush=True)
manifest["sources"]["july"] = done

# ---- repo_kimi_team_recon: unique skill dirs by SKILL.md sha ----
print("recon tree...", flush=True)
rtree = tree_recursive("repo_kimi_team_recon", "master")
rskills = [(x["path"], x["sha"]) for x in rtree if x["type"] == "blob" and x["path"].lower().endswith("skill.md")]
print(f"  {len(rskills)} SKILL.md files", flush=True)
by_sha = {}
for path, sha in rskills:
    by_sha.setdefault(sha, path)
print(f"  {len(by_sha)} unique SKILL.md contents", flush=True)
kept_dirs = {os.path.dirname(p) for p in by_sha.values()}
dir_files = {}
for x in rtree:
    if x["type"] != "blob":
        continue
    d = os.path.dirname(x["path"])
    if d in kept_dirs:
        dir_files.setdefault(d, []).append((x["path"], x["sha"]))
jobs = [(p, s, d) for d, fl in dir_files.items() for (p, s) in fl]
print(f"  {len(jobs)} blobs to download across {len(dir_files)} dirs", flush=True)
def w_recon(job):
    path, sha, d = job
    data = get_blob("repo_kimi_team_recon", sha)
    skill = os.path.basename(d)
    fp = os.path.join(STAGE, "recon", skill, os.path.relpath(path, d))
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    open(fp, "wb").write(data)
    return skill
with ThreadPoolExecutor(max_workers=12) as ex:
    skills = list(ex.map(w_recon, jobs))
manifest["sources"]["recon"] = {"unique_skillmd": len(by_sha), "dirs": sorted(set(skills)),
                                "total_skillmd_files": len(rskills)}

# ---- experimental-crisis: the 8 skill dirs ----
print("crisis tree...", flush=True)
ctree = tree_recursive("experimental-crisis", "main")
cjobs = [(x["path"], x["sha"]) for x in ctree if x["type"] == "blob" and
         (x["path"].startswith("skills/") or x["path"].startswith("overlay_skills/"))]
def w_crisis(item):
    path, sha = item
    data = get_blob("experimental-crisis", sha)
    parts = path.split("/")
    skill = parts[1]
    fp = os.path.join(STAGE, "crisis", skill, *parts[2:])
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    open(fp, "wb").write(data)
    return skill
with ThreadPoolExecutor(max_workers=12) as ex:
    cskills = list(ex.map(w_crisis, cjobs))
manifest["sources"]["crisis"] = {"dirs": sorted(set(cskills)), "files": len(cjobs)}
print(f"  crisis: {len(cjobs)} files, dirs={sorted(set(cskills))}", flush=True)

json.dump(manifest, open(f"{STAGE}/manifest.json", "w"), indent=1)
print("MANIFEST WRITTEN", flush=True)
