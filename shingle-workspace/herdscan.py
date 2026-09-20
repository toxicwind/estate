#!/usr/bin/env python3
"""herdscan — secret-hygiene scanner for the herd repo (consolidated v1+v2+v3).

Clones the herd repo shallow, scans for leaked secrets, and NEVER prints
secret values — only value shapes (letters->A, digits->9) and placeholder
classification. Replaces the old herdscan.py / herdscan2.py / herdscan3.py
trio, which duplicated the same clone+scan loop.

Usage:
    python3 herdscan.py [--keep] [--repo URL] [--dir PATH] [--branch BR]

Exit codes: 0 = scan complete (findings are informational), 1 = usage/tool error.
"""
import argparse
import os
import random
import re
import shutil
import subprocess
import sys

DEFAULT_REPO = "https://github.com/toxicwind/herd"

HIGH_SIGNAL = [
    r"AKIA[0-9A-Z]{16}",
    r"ghp_[A-Za-z0-9]{36}",
    r"gho_[A-Za-z0-9]{36}",
    r"sk-ant-[A-Za-z0-9-]+",
    r"sk-proj-[A-Za-z0-9-]+",
    r"BEGIN [A-Z ]*PRIVATE KEY",
    r"aws_secret_access_key",
]

ASSIGN_RE = re.compile(
    r"(?i)(api[_-]?key|secret|passwd|password)\s*[:=]\s*[\"']?"
    r"([A-Za-z0-9_\-\$\{\}\<\>\.]{6,})"
)

# files that historically carried inline credentials (from herdscan v2/v3)
SPOT_FILES = [
    "mesh/gateway/bench/docker-compose.yml",
    "mesh/gateway/bench/README.md",
    "mesh/gateway/bench/mcpcall_test.go",
    "mesh/gateway/cmd/mcpproxy/status_cmd_test.go",
    "mesh/gateway/cmd/mcpproxy/status_cmd.go",
    "mesh/gateway/contrib/linux-repos/apt-publish.sh",
]

PLACEHOLDER_RE = re.compile(
    r"(?i)^(\$\{|<|example|changeme|test|dummy|placeholder|x+|your-|todo|"
    r"none|null|\"\"|''|true|false)$"
)


def shape(v):
    """Render value shape only: letters->A, digits->9, keep separators."""
    s = re.sub(r"[A-Za-z]", "A", v)
    s = re.sub(r"[0-9]", "9", s)
    return s[:40]


def is_placeholder(v):
    return bool(PLACEHOLDER_RE.match(v) or len(v) < 8 or "${" in v)


def run(cmd, cwd=None, timeout=120):
    return subprocess.run(
        cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout
    )


def find_files(root, name_re):
    """Find files matching a regex; prefers fd, falls back to os.walk."""
    fd = shutil.which("fd")
    if fd:
        out = run([fd, "-H", "-t", "f", name_re, "."], cwd=root)
        return [l for l in out.stdout.splitlines() if l.strip()]
    pat = re.compile(name_re)
    hits = []
    for dirpath, _, files in os.walk(root):
        for f in files:
            if pat.search(f):
                hits.append(os.path.relpath(os.path.join(dirpath, f), root))
    return hits


def rg_hits(root, pattern, paths=(".",), whole_word=False):
    """High-signal hits via rg if present, else pure-python fallback."""
    rg = shutil.which("rg")
    cmd = [rg, "-l", "-i", "--no-messages", pattern] if rg else None
    if rg:
        for p in paths:
            c = cmd + ([p] if p != "." else ["."])
            if p.startswith("!"):
                continue
            out = run(c, cwd=root)
            for line in out.stdout.splitlines():
                if line.strip():
                    yield line.strip()
        return
    # fallback: walk + regex (slower, same semantics)
    cre = re.compile(pattern, re.I)
    for dirpath, _, files in os.walk(root):
        for f in files:
            fp = os.path.join(dirpath, f)
            try:
                with open(fp, errors="replace") as fh:
                    txt = fh.read(200000)
            except OSError:
                continue
            if cre.search(txt):
                yield os.path.relpath(fp, root)


def main():
    ap = argparse.ArgumentParser(description="herd repo secret-hygiene scan")
    ap.add_argument("--keep", action="store_true", help="keep the clone dir")
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--dir", default=None, help="scan existing dir instead of cloning")
    ap.add_argument("--branch", default=None)
    args = ap.parse_args()

    if args.dir:
        d = os.path.abspath(args.dir)
        if not os.path.isdir(d):
            print(f"error: --dir not found: {d}", file=sys.stderr)
            return 1
        cloned = False
    else:
        d = f"/home/toxic/herd-scan-{random.randint(10000, 99999)}"
        cmd = ["git", "clone", "--depth", "1", "-q", args.repo, d]
        if args.branch:
            cmd[4:4] = ["-b", args.branch]
        r = run(cmd, timeout=300)
        if r.returncode != 0 or not os.path.isdir(d):
            print(f"error: clone failed: {r.stderr.strip()[:200]}", file=sys.stderr)
            return 1
        cloned = True
    print("scanning", d)

    # 1. .env files anywhere
    envs = find_files(d, r"^\.env")
    print(f"--- .env files: {len(envs)}")
    for e in envs[:30]:
        print("  " + e)

    # 2. high-signal secret patterns (mesh/ first, then whole repo)
    print("--- high-signal hits in mesh/:")
    hits = sorted(set(rg_hits(d, "|".join(HIGH_SIGNAL), ("mesh",))))
    print("\n".join("  " + h for h in hits) or "  (none)")
    print("--- high-signal hits outside mesh/:")
    hits = sorted(set(rg_hits(d, "|".join(HIGH_SIGNAL), (".",))))
    hits = [re.sub(r"^\./", "", h) for h in hits]  # normalize rg's ./ prefix
    hits = [h for h in hits if not h.startswith("mesh/")]
    print("\n".join("  " + h for h in hits[:40]) or "  (none)")

    # 3. assignment-style key=value scan with shape-only reporting
    print("--- assignment-style scan (shape only, never values):")
    seen = set()
    total = 0
    targets = list(SPOT_FILES)
    # plus every .env found above
    targets += [e for e in envs if e not in targets]
    for f in targets:
        p = os.path.join(d, f)
        if not os.path.isfile(p):
            continue
        try:
            txt = open(p, errors="replace").read(500000)
        except OSError as e:
            print(f"  {f}: UNREADABLE {e}")
            continue
        local = 0
        for m in ASSIGN_RE.finditer(txt):
            key, val = m.group(1), m.group(2).strip("\"'")
            if val in seen:
                continue
            seen.add(val)
            local += 1
            total += 1
            ph = is_placeholder(val)
            if not ph or local <= 5:  # always show non-placeholders
                print(f"  {f}: key={key} shape={shape(val)} "
                      f"placeholder_like={ph} len={len(val)}")
        if local == 0:
            print(f"  {f}: (no assignment matches)")
    print(f"--- total distinct assignment matches: {total}")

    if cloned and not args.keep:
        shutil.rmtree(d, ignore_errors=True)
        print("cleaned up")
    elif cloned:
        print(f"kept clone at {d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
