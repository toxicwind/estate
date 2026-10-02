import json, sys, urllib.request
sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import add_surrogate_to_request, read_json_response

BASE = "https://api.github.com/repos/toxicwind/herd"
UA = {"Accept": "application/vnd.github+json", "User-Agent": "shingle-readme-fix"}

def get(path):
    req = urllib.request.Request(BASE + path, headers=UA)
    add_surrogate_to_request(req, "custom.github", allowed_hosts=["api.github.com"])
    return read_json_response(urllib.request.urlopen(req, timeout=30))

def get_raw(url):
    req = urllib.request.Request(url, headers=UA)
    add_surrogate_to_request(req, "custom.github", allowed_hosts=["api.github.com"])
    return read_json_response(urllib.request.urlopen(req, timeout=30))

# 1. recursive tree
tree = get("/git/trees/main?recursive=1")
paths = {t["path"] for t in tree["tree"] if t["type"] == "blob"}
print("total blobs:", len(paths))
for p in ["README.md", "README_ASTMATRIX_V2.md", "internal/bench/orchestrator.go",
          "docker/unified/build-image.sh", ".github/workflows/unified-docker.yml",
          ".github/workflows/tectonic-drift.yml", "lib/lens-orchestrator.js",
          ".env.example", "Makefile", "internal/server/models_sse.go",
          "internal/astmatrix/circuit.go", "internal/astmatrix/ratelimit.go",
          "internal/astmatrix/ui.go", "internal/config/model_config.go",
          "internal/process/process_command.go"]:
    print(("OK  " if p in paths else "MISS"), p)
lenses = sorted(p for p in paths if p.startswith("src/_11ty/lenses/"))
print("lenses:", len(lenses), lenses[:8])
provs = [p for p in paths if p.startswith("internal/astmatrix/")]
print("astmatrix files:", len(provs))
strategies = set()
# 2. spot-check file contents
def content(path):
    d = get("/contents/" + path + "?ref=main")
    import base64
    return base64.b64decode(d["content"]).decode("utf-8", "replace")

ud = content(".github/workflows/unified-docker.yml")
for line in ud.splitlines():
    if "DOCKER_IMAGE_TAG" in line:
        print("UD IMG:", line.strip()[:120])
bi = content("docker/unified/build-image.sh")
print("rootless note:", [l.strip()[:100] for l in bi.splitlines() if "buildx" in l.lower()][:4])
rm = content("README.md")
print("README head:", rm.splitlines()[0][:80], "| len:", len(rm))
print("README mentions herd:", rm.lower().count("herd"))
