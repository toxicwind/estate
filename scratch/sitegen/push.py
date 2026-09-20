#!/usr/bin/env python3
"""push.py - push docs/ site + new data JSONs to toxicwind/nvidia-nim-model-probe
via GitHub Contents API, then enable GitHub Pages."""
import sys, json, base64, os, re, urllib.request, urllib.error
sys.path.insert(0, "/home/hatch/workspace/skills/shared")
import trusted_dns
trusted_dns.patch_socket()
sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import add_surrogate_to_request

REPO = "toxicwind/nvidia-nim-model-probe"
API = f"https://api.github.com/repos/{REPO}"
HOSTS = ["api.github.com"]
UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
SITE = "/home/hatch/workspace/sitegen/docs"
DATA = "/home/hatch/workspace/skills/nvidia-nim-loader"

FILES = [
    ("docs/index.html", f"{SITE}/index.html"),
    ("docs/models.html", f"{SITE}/models.html"),
    ("docs/tooluse.html", f"{SITE}/tooluse.html"),
    ("docs/fuzz.html", f"{SITE}/fuzz.html"),
    ("docs/cards.html", f"{SITE}/cards.html"),
    ("docs/methodology.html", f"{SITE}/methodology.html"),
    ("docs/assets/style.css", f"{SITE}/assets/style.css"),
    ("docs/assets/app.js", f"{SITE}/assets/app.js"),
    ("data/fuzz_max_2026-09-14.json", f"{DATA}/fuzz_max_2026-09-14.json"),
    ("data/tooluse_probe_2026-09-14.json", f"{DATA}/tooluse_probe_2026-09-14.json"),
    ("data/card_xref_2026-09-14.json", f"{DATA}/card_xref_2026-09-14.json"),
]

def req(method, url, payload=None):
    r = urllib.request.Request(url, method=method,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Content-Type": "application/json",
                 "Accept": "application/vnd.github+json"})
    add_surrogate_to_request(r, "custom.github", allowed_hosts=HOSTS)
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as e:
        return e.code, e.read(500).decode(errors="replace")

def get_sha(path):
    s, d = req("GET", f"{API}/contents/{path}")
    return d["sha"] if s == 200 else None

def sanitize_bytes(b):
    t = b.decode("utf-8")
    assert "nvapi-" not in t, f"RAW KEY in file - ABORT"
    t = UUID_RE.sub("REDACTED", t)
    return t.encode()

pushed, failed = [], []
for repo_path, local in FILES:
    raw = open(local, "rb").read()
    clean = sanitize_bytes(raw)
    payload = {"message": "GitHub Pages site: full probe data explorer",
               "content": base64.b64encode(clean).decode()}
    sha = get_sha(repo_path)
    if sha:
        payload["sha"] = sha
    s, d = req("PUT", f"{API}/contents/{repo_path}", payload)
    if s in (200, 201):
        pushed.append((repo_path, len(clean)))
        print(f"OK {repo_path} ({len(clean)}b)", flush=True)
    else:
        failed.append((repo_path, s, str(d)[:200]))
        print(f"FAIL {repo_path}: {s} {str(d)[:200]}", flush=True)

print(f"\n{len(pushed)} pushed, {len(failed)} failed", flush=True)

# enable Pages
s, d = req("POST", f"{API}/pages", {"source": {"branch": "main", "path": "/docs"}})
print("pages POST:", s, json.dumps(d)[:300] if isinstance(d, dict) else str(d)[:300], flush=True)
s, d = req("GET", f"{API}/pages")
print("pages GET:", s, flush=True)
if isinstance(d, dict):
    print("html_url:", d.get("html_url"), flush=True)
    print("status:", d.get("status"), flush=True)
    print(json.dumps(d, indent=1)[:800], flush=True)
