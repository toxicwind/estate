#!/bin/bash
# Cut one disposable workspace with a worktree per parent-registry repo.
# workmux and super-board are single-repo; this is the cross-remote step.
set -euo pipefail
name="${1:-}"
if [[ -z "$name" || ! "$name" =~ ^[a-z0-9][a-z0-9-]{0,40}$ ]]; then
  echo "usage: $0 <workspace-name>" >&2
  exit 64
fi
root="/home/toxic/estate"
reg="$root/config/repos.toml"
dest="$root/var/workspaces/$name"
mkdir -p "$dest"
python3 - "$reg" "$dest" "$name" << 'PY'
import pathlib, subprocess, sys
reg, dest, name = sys.argv[1:]
text = pathlib.Path(reg).read_text().splitlines()
repos = {}
cur = None
for ln in text:
    s = ln.strip()
    if s.startswith("[") and s.endswith("]") and "." not in s:
        cur = s[1:-1]
        repos[cur] = {}
    elif cur and "=" in s and not s.startswith("#"):
        k, v = s.split("=", 1)
        repos[cur][k.strip()] = v.strip().strip('"')
rows = ["# workspace " + name, "", "| repo | role | branch | path |", "|---|---|---|---|"]
for repo, meta in repos.items():
    src = meta.get("path", "")
    branch = "ws/" + name
    target = pathlib.Path(dest) / repo
    if not src or not pathlib.Path(src).exists():
        rows.append(f"| {repo} | {meta.get('role','')} | missing | `{src}` |")
        continue
    if target.exists():
        rows.append(f"| {repo} | {meta.get('role','')} | existing | `{target}` |")
        continue
    proc = subprocess.run(["git", "-C", src, "worktree", "add", "-b", branch, str(target), meta.get("branch", "main")], capture_output=True, text=True)
    if proc.returncode != 0 and "already exists" in proc.stderr:
        proc = subprocess.run(["git", "-C", src, "worktree", "add", str(target), branch], capture_output=True, text=True)
    status = "ok" if proc.returncode == 0 else "failed"
    rows.append(f"| {repo} | {meta.get('role','')} | {branch} {status} | `{target}` |")
    if proc.returncode != 0:
        rows.append("")
        rows.append("```")
        rows.append(proc.stderr.strip()[:500])
        rows.append("```")
path = pathlib.Path(dest) / "WORKSPACE.md"
path.write_text("\n".join(rows) + "\n")
print(path)
PY
