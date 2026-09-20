import subprocess, random, os

SOV = "/home/toxic/sovereign"
WT = f"/home/toxic/modelpush-{random.randint(10000,99999)}"
KDL = "tau/engine/packages/catalog/src/compat/rules/auth/nvidia.kdl"

def sh(*a, cwd=SOV):
    r = subprocess.run(a, capture_output=True, text=True, cwd=cwd, timeout=120)
    return r

# 1. fresh clean worktree at origin/main
r = sh("git", "worktree", "add", WT, "origin/main")
print("worktree add:", (r.stdout.strip() or "") + (r.stderr.strip() or ""))
if r.returncode != 0:
    raise SystemExit("worktree add failed")

# 2. apply the one-line fix
p = os.path.join(WT, KDL)
txt = open(p).read()
old = 'model="nvidia/llama-3.1-nemotron-70b-instruct"'
assert txt.count(old) == 1, f"unexpected count {txt.count(old)}"
open(p, "w").write(txt.replace(old, 'model="openai/gpt-oss-20b"'))
print("patched in worktree")

# 3. verify no other pending changes in worktree, commit, push
r = sh("git", "status", "--porcelain", cwd=WT)
print("worktree status:", r.stdout.strip())
r = sh("git", "add", KDL, cwd=WT)
r = sh("git", "commit", "-m",
       "fix: tau nvidia auth validation uses live fast model (openai/gpt-oss-20b); "
       "nvidia/llama-3.1-nemotron-70b-instruct is 404-dead on NIM",
       cwd=WT)
print("commit:", r.stdout.strip().split("\n")[0] if r.returncode == 0 else r.stderr.strip()[:200])
sha = sh("git", "rev-parse", "--short", "HEAD", cwd=WT).stdout.strip()
print("sha:", sha)
r = sh("git", "push", "origin", "HEAD:main", cwd=WT)
print("push rc:", r.returncode, (r.stderr.strip() or "")[-200:])

# 4. cleanup worktree
sh("git", "worktree", "remove", "--force", WT)
print("worktree removed")
