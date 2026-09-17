#!/usr/bin/env python3
"""git-push-one.py: Push one file to GitHub repo with per-repo identity."""
import os, sys, subprocess, base64, requests
from pathlib import Path
from datetime import datetime

def ts():
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]

def api_push(repo, path, content, message, pat):
    headers = {"Authorization": f"Bearer {pat}", "Accept": "application/vnd.github+json"}
    r = requests.get(f"https://api.github.com/repos/toxicwind/{repo}/contents/{path}", headers=headers, timeout=10)
    sha = r.json().get("sha") if r.status_code == 200 else None
    b64 = base64.b64encode(content.encode() if isinstance(content, str) else content).decode()
    payload = {"message": message, "content": b64}
    if sha: payload["sha"] = sha
    r = requests.put(f"https://api.github.com/repos/toxicwind/{repo}/contents/{path}", headers=headers, json=payload, timeout=15)
    return r.status_code, r.json()

def git_push(repo, filepath, message, pat):
    pat = pat or os.environ.get("GITHUB_TOKEN", "")
    if not pat:
        print(f"[{ts()}] ERROR: No PAT"); return 1
    filepath = Path(filepath)
    if not filepath.exists():
        print(f"[{ts()}] ERROR: {filepath} not found"); return 1
    
    workspace = Path("/mnt/agents/output/repos")
    workspace.mkdir(parents=True, exist_ok=True)
    repo_dir = workspace / repo
    
    if not (repo_dir / ".git").exists():
        print(f"[{ts()}] Cloning {repo}...")
        url = f"https://toxicwind:{pat}@github.com/toxicwind/{repo}.git"
        r = subprocess.run(["git", "clone", "--depth", "1", url, str(repo_dir)], capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            print(f"[{ts()}] Clone failed: {r.stderr[:200]}"); return 1
    
    # Per-repo identity (NO --global)
    subprocess.run(["git", "config", "user.email", "toxicwind@users.noreply.github.com"], cwd=str(repo_dir), capture_output=True)
    subprocess.run(["git", "config", "user.name", "toxicwind"], cwd=str(repo_dir), capture_output=True)
    
    target = repo_dir / filepath.name
    import shutil
    shutil.copy2(filepath, target)
    subprocess.run(["git", "add", str(target)], cwd=str(repo_dir), capture_output=True)
    
    msg = message or f"feat: add {filepath.name} — {ts()}"
    r = subprocess.run(["git", "commit", "-m", msg], cwd=str(repo_dir), capture_output=True, text=True)
    if r.returncode != 0 and "nothing to commit" not in r.stderr.lower():
        print(f"[{ts()}] Commit note: {r.stderr[:100]}")
    
    r = subprocess.run(["git", "push", "origin", "main"], cwd=str(repo_dir), capture_output=True, text=True, timeout=20)
    if r.returncode == 0:
        print(f"[{ts()}] PUSHED {filepath.name} -> toxicwind/{repo}")
    else:
        print(f"[{ts()}] Push failed: {r.stderr[:200]}")
    return r.returncode

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("repo")
    p.add_argument("file")
    p.add_argument("-m", "--message", default=None)
    p.add_argument("--pat", default=os.environ.get("GITHUB_TOKEN", ""))
    p.add_argument("--api", action="store_true", help="Use GitHub API instead of git")
    args = p.parse_args()
    if args.api:
        content = Path(args.file).read_bytes()
        msg = args.message or f"add {Path(args.file).name}"
        status, result = api_push(args.repo, Path(args.file).name, content, msg, args.pat)
        print(f"[{ts()}] {args.file} -> {args.repo}: {status}")
        if status in [200, 201]:
            print(f"  OK: {result.get('content', {}).get('html_url', 'pushed')}")
        else:
            print(f"  ERR: {result.get('message', result)[:100]}")
    else:
        sys.exit(git_push(args.repo, args.file, args.message, args.pat))
