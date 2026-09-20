#!/usr/bin/env python3
"""Second-pass triage on HEAD files. Runs on awrawr-pc.

For each non-placeholder generic_secret_assign / high_entropy finding at HEAD,
re-examines the source line and classifies:
  - CODE: value is a code expression (contains '(' / '::' / '=>', or bare identifier)
  - QUOTED_LITERAL: value was a quoted string -> report w/ entropy + redacted
  - PLACEHOLDER: matches placeholder heuristics
Prints redacted JSON. Raw values never leave this host.
"""
import json
import math
import os
import re
import subprocess
import sys
from collections import Counter

KEY_RX = re.compile(
    r"(?i)\b(password|passwd|pwd|secret|api[_-]?key|apikey|auth[_-]?token|"
    r"access[_-]?token|client[_-]?secret|db[_-]?pass(?:word)?|token)\b"
    r"\s*[:=]\s*")
STR_RX = re.compile(r"""^(['"])((?:\\.|(?!\1).){8,}?)\1""")

_PLACEHOLDER_SUBSTR = ("example", "placeholder", "changeme", "your_", "_here",
                       "xxx", "***", "<", ">", "redacted")


def is_placeholder(v):
    w = v.strip().strip("'\"").lower()
    if len(set(w)) <= 2:
        return True
    return any(s in w for s in _PLACEHOLDER_SUBSTR)


def shannon(s):
    n = len(s)
    if not n:
        return 0.0
    return -sum((c / n) * math.log2(c / n) for c in Counter(s).values())


def redact(v):
    return "***" if len(v) <= 10 else v[:4] + chr(8230) + v[-2:]


def git(repo, *a):
    return subprocess.run(["git", "-C", repo] + list(a),
                          capture_output=True, text=True).stdout


def triage_repo(repo):
    head = git(repo, "rev-parse", "HEAD").strip()
    files = {}
    for line in git(repo, "ls-tree", "-r", "--name-only", "HEAD").splitlines():
        files[line] = True
    report = []
    for rel in files:
        p = os.path.join(repo, rel)
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError:
            continue
        if "\x00" in text[:8192] or len(text) > 2000000:
            continue
        for i, ln in enumerate(text.split("\n"), 1):
            for m in KEY_RX.finditer(ln):
                rest = ln[m.end():].lstrip()
                sm = STR_RX.match(rest)
                if sm:
                    val = sm.group(2)
                    kind = "QUOTED_LITERAL"
                else:
                    tok = re.match(r"[^\s#,;]{8,}", rest)
                    if not tok:
                        continue
                    val = tok.group(0)
                    kind = "CODE" if ("(" in val or "::" in val or val[0].islower() and "." in val) else "BARE"
                if is_placeholder(val):
                    kind = "PLACEHOLDER"
                if kind == "CODE":
                    continue
                report.append({
                    "path": rel, "line": i, "kind": kind,
                    "key": m.group(1), "len": len(val),
                    "entropy": round(shannon(val), 2),
                    "redacted": redact(val),
                })
    # high-entropy tokens in non-test src files at HEAD
    ENT_RX = re.compile(r"[A-Za-z0-9_+/=.$-]{24,}")
    for rel in files:
        if not ("/src/" in rel or rel.endswith((".rs", ".py", ".ts", ".js", ".go"))):
            continue
        if "test" in rel.lower() or "fixture" in rel.lower():
            continue
        p = os.path.join(repo, rel)
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError:
            continue
        for m in ENT_RX.finditer(text):
            tok = m.group(0).strip(".-=$")
            if len(tok) < 24 or shannon(tok) < 4.6 or is_placeholder(tok):
                continue
            if "/" in tok and "." in tok or tok.count("-") > 6:
                continue
            line = text.count("\n", 0, m.start()) + 1
            report.append({"path": rel, "line": line, "kind": "HIGH_ENTROPY",
                           "len": len(tok), "entropy": round(shannon(tok), 2),
                           "redacted": redact(tok)})
    return {"head": head[:12], "items": report}


out = {}
for repo in sys.argv[1:]:
    out[repo] = triage_repo(repo)
json.dump(out, sys.stdout, indent=1)
sys.stdout.write("\n")
