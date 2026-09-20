#!/usr/bin/env python3
"""History-wide hunt for live-looking secret literals. Runs on awrawr-pc.

Scans every blob in --all history for QUOTED string literals assigned to
secret-ish keys (password/secret/api_key/token/...) with high entropy and
length >= 16, excluding placeholders. Attributes each hit to introducing
commits via git log -S. Also flags private-key blocks and known token
prefixes (ghp_/sk-ant-/nvapi-/xoxb-/AKIA) anywhere in history.

Prints redacted JSON. Raw values never leave this host.
"""
import hashlib
import json
import math
import re
import subprocess
import sys
from collections import Counter

KEY_RX = re.compile(
    r"(?i)\b(password|passwd|pwd|secret|api[_-]?key|apikey|auth[_-]?token|"
    r"access[_-]?token|client[_-]?secret|db[_-]?pass(?:word)?|token)\b"
    r"\s*[:=]\s*")
STR_RX = re.compile(r"""^(['"])((?:\\.|(?!\1).){8,}?)\1""")
HARD_RX = [
    ("github_token", re.compile(r"\b(ghp_[A-Za-z0-9]{36}|gho_[A-Za-z0-9]{36}|ghu_[A-Za-z0-9]{36}|ghr_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{22,})\b")),
    ("anthropic_key", re.compile(r"\bsk-ant-[A-Za-z0-9-]{20,}\b")),
    ("openai_key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9]{20,}\b")),
    ("nvidia_key", re.compile(r"\bnvapi-[A-Za-z0-9_-]{16,}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("aws_access_key", re.compile(r"\b(AKIA|ASIA|ABIA|ACCA)[0-9A-Z]{16}\b")),
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\b")),
    ("telegram_token", re.compile(r"\b[0-9]{8,10}:[A-Za-z0-9_-]{35}\b")),
]

_PH_SUB = ("example", "placeholder", "changeme", "your_", "_here", "xxx",
           "***", "<", ">", "redacted", "test", "demo", "sample", "fake")


def is_placeholder(v):
    w = v.strip().strip("'\"").lower()
    if len(set(w)) <= 2:
        return True
    return any(s in w for s in _PH_SUB)


def shannon(s):
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in Counter(s).values()) if n else 0.0


def redact(v):
    return "***" if len(v) <= 10 else v[:4] + chr(8230) + v[-2:]


def fp(pat, v):
    return "sha256:" + hashlib.sha256(("%s:%s" % (pat, v)).encode()).hexdigest()[:16]


def git(repo, *a, raw=False):
    r = subprocess.run(["git", "-C", repo] + list(a),
                       capture_output=True, text=not raw)
    return r.stdout


def hunt(repo):
    objs = git(repo, "rev-list", "--all", "--objects").splitlines()
    shas = [l.split(" ", 1)[0] for l in objs if l.strip()]
    p = subprocess.run(["git", "-C", repo, "cat-file", "--batch-check"],
                       input="\n".join(shas).encode(), capture_output=True)
    blob_paths = {}
    for line in p.stdout.decode(errors="replace").splitlines():
        pr = line.split(" ")
        if len(pr) >= 2 and pr[1] == "blob":
            blob_paths.setdefault(pr[0], set())
    for line in objs:
        pr = line.split(" ", 1)
        if len(pr) == 2 and pr[0] in blob_paths:
            blob_paths[pr[0]].add(pr[1])
    hits = []
    for blob, paths in blob_paths.items():
        data = git(repo, "cat-file", "-p", blob, raw=True)
        if b"\x00" in data[:8192] or len(data) > 2000000:
            continue
        text = data.decode("utf-8", errors="replace")
        rel = sorted(paths)[0]
        # hard token prefixes
        for name, rx in HARD_RX:
            for m in rx.finditer(text):
                v = m.group(0)
                line = text.count("\n", 0, m.start()) + 1
                hits.append({"kind": name, "blob": blob, "path": rel,
                             "paths": sorted(paths), "line": line,
                             "redacted": redact(v), "fingerprint": fp(name, v),
                             "placeholder": is_placeholder(v), "_raw": v})
        # quoted literals on secret keys
        for i, ln in enumerate(text.split("\n"), 1):
            for m in KEY_RX.finditer(ln):
                sm = STR_RX.match(ln[m.end():].lstrip())
                if not sm:
                    continue
                v = sm.group(2)
                if len(v) < 16 or shannon(v) < 4.5 or is_placeholder(v):
                    continue
                hits.append({"kind": "quoted_secret_literal", "blob": blob,
                             "path": rel, "paths": sorted(paths), "line": i,
                             "key": m.group(1), "entropy": round(shannon(v), 2),
                             "redacted": redact(v), "fingerprint": fp("qsl", v),
                             "placeholder": False, "_raw": v})
    seen, uniq = set(), []
    for h in hits:
        k = (h["fingerprint"], h["blob"])
        if k not in seen:
            seen.add(k)
            uniq.append(h)
    for h in uniq:
        out = git(repo, "log", "--all", "--format=%H|%ci|%s", "-S", h["_raw"],
                  "--", h["path"])
        commits = []
        for line in out.splitlines():
            pr = line.split("|", 2)
            if len(pr) == 3:
                commits.append({"sha": pr[0][:12], "date": pr[1],
                                "subject": pr[2][:90]})
        h["commits"] = commits
        del h["_raw"]
    return {"blobs": len(blob_paths), "hits": uniq}


out = {repo: hunt(repo) for repo in sys.argv[1:]}
json.dump(out, sys.stdout, indent=1)
sys.stdout.write("\n")
