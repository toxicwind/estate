import subprocess, base64, json, os

SOV = "/home/toxic/sovereign"
KDL = "tau/engine/packages/catalog/src/compat/rules/auth/nvidia.kdl"
REPO = "toxicwind/sovereign-projects"

def sh(*a, cwd=SOV):
    return subprocess.run(a, capture_output=True, text=True, cwd=cwd,
                          timeout=120)

# 1. sanity: working file vs origin/main must differ by exactly the one line
r = sh("git", "show", f"origin/main:{KDL}")
orig = r.stdout
work = open(os.path.join(SOV, KDL)).read()
import difflib
d = list(difflib.unified_diff(orig.split("\n"), work.split("\n"), lineterm=""))
print("diff lines:", len(d))
for line in d:
    print(line[:160])
changed = [l for l in d if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))]
ok = (len(changed) == 2 and "llama-3.1-nemotron-70b-instruct" in changed[0]
      and "openai/gpt-oss-20b" in changed[1])
print("exactly-one-line-change:", ok)
if not ok:
    raise SystemExit("unexpected diff, aborting")

# 2. cleanup any partial worktree from the failed attempt
r = sh("git", "worktree", "list")
print("worktrees:", r.stdout.strip().split("\n")[0][:80], "...")
for line in r.stdout.split("\n"):
    if "modelpush-" in line:
        wt = line.split()[0]
        sh("git", "worktree", "remove", "--force", wt)
        print("removed stale worktree", wt)

# 3. get current blob sha on main via API, then PUT the patched file
r = subprocess.run(
    ["gh", "api", f"repos/{REPO}/contents/{KDL}?ref=main", "--jq", ".sha"],
    capture_output=True, text=True, timeout=60)
sha = r.stdout.strip()
print("blob sha on main:", sha[:12])
b64 = base64.b64encode(work.encode()).decode()
payload = json.dumps({
    "message": ("fix: tau nvidia auth validation uses live fast model "
                "(openai/gpt-oss-20b); nvidia/llama-3.1-nemotron-70b-instruct "
                "is 404-dead on NIM"),
    "content": b64,
    "sha": sha,
    "branch": "main",
})
r = subprocess.run(
    ["gh", "api", "--method", "PUT", f"repos/{REPO}/contents/{KDL}",
     "--input", "-"],
    input=payload, capture_output=True, text=True, timeout=120)
if r.returncode != 0:
    print("PUT FAILED:", r.stderr.strip()[:500])
    raise SystemExit(1)
resp = json.loads(r.stdout)
print("committed:", resp["commit"]["sha"][:12], "on", resp["commit"].get("html_url", ""))
