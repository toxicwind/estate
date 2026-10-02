#!/usr/bin/env python3
"""metaaivm harvest: fetch repo meta, README, issues, PRs for candidate repos."""
import base64, json, os, sys

sys.path.insert(0, os.path.expanduser("~/workspace/skills/github/bin"))
import importlib.util
spec = importlib.util.spec_from_file_location("gh", os.path.expanduser("~/workspace/skills/github/bin/gh.py"))
gh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gh)

REPOS = ["sisimomo/aivm", "NillionNetwork/nillion-aivm", "toxicwind/metaclaw-runtime"]
OUT = os.path.expanduser("~/workspace/metaaivm-harvest/repos")

def safe_get(path, params=None):
    try:
        return gh.api_get(path, params)
    except Exception as e:
        return {"_error": str(e)}

for r in REPOS:
    d = os.path.join(OUT, r.replace("/", "-"))
    os.makedirs(d, exist_ok=True)
    print("harvesting", r, file=sys.stderr)
    meta = safe_get("/repos/" + r)
    with open(os.path.join(d, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    readme = safe_get("/repos/" + r + "/contents/README.md")
    if isinstance(readme, dict) and readme.get("content"):
        try:
            raw = base64.b64decode(readme["content"]).decode("utf-8", "replace")
        except Exception as e:
            raw = "_decode error: %s_" % e
    else:
        raw = "_no README: %s_" % json.dumps(readme)[:200]
    with open(os.path.join(d, "README.md"), "w") as f:
        f.write(raw)
    issues = safe_get("/repos/" + r + "/issues", {"state": "all", "per_page": 30})
    with open(os.path.join(d, "issues.json"), "w") as f:
        json.dump(issues, f, indent=2)
    prs = safe_get("/repos/" + r + "/pulls", {"state": "all", "per_page": 30})
    with open(os.path.join(d, "prs.json"), "w") as f:
        json.dump(prs, f, indent=2)
    n_i = len(issues) if isinstance(issues, list) else 0
    n_p = len(prs) if isinstance(prs, list) else 0
    print("  readme bytes:", len(raw), "issues:", n_i, "prs:", n_p, file=sys.stderr)
print("done", file=sys.stderr)
