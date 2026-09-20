#!/usr/bin/env python3
"""Self-contained history secrets sweep. Runs on awrawr-pc.

Usage: python3 sweep_all.py <repo-dir> [<repo-dir>...]
For each repo dir: walks every blob reachable from --all history,
scans contents with the secret pattern library, attributes each finding
to introducing commits via git log -S, lists tracked store-like filenames.
Prints redacted JSON to stdout. Raw values never leave this host.
"""
import hashlib
import json
import math
import os
import re
import subprocess
import sys
from collections import Counter

_RAW = [
    ("github_token",
     r"\b(ghp_[A-Za-z0-9]{36}|gho_[A-Za-z0-9]{36}|ghu_[A-Za-z0-9]{36}"
     r"|ghr_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{22,})\b",
     0, "critical"),
    ("aws_access_key",
     r"\b(AKIA|ASIA|ABIA|ACCA)[0-9A-Z]{16}\b",
     0, "high"),
    ("aws_secret",
     r"(?i)\baws[_-]?secret[_-]?access[_-]?key\b\s*[:=]\s*['\"]?"
     r"([A-Za-z0-9/+=]{40})['\"]?",
     1, "critical"),
    ("gcp_service_key",
     r'"type"\s*:\s*"service_account"',
     0, "high"),
    ("private_key",
     r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
     0, "critical"),
    ("jwt",
     r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\b",
     0, "high"),
    ("slack_token",
     r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b",
     0, "critical"),
    ("discord_token",
     r"\b(?:[MN][A-Za-z0-9_-]{23}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{27}"
     r"|mfa\.[A-Za-z0-9_-]{84})\b",
     0, "critical"),
    ("telegram_token",
     r"\b[0-9]{8,10}:[A-Za-z0-9_-]{35}\b",
     0, "high"),
    ("stripe_key",
     r"\b(?:sk_live|rk_live|whsec)_[A-Za-z0-9]{10,}\b",
     0, "critical"),
    ("npm_token",
     r"\bnpm_[A-Za-z0-9]{36}\b",
     0, "high"),
    ("pypi_token",
     r"\bpypi-AgEIcHlwaS5vcmc[A-Za-z0-9_-]{20,}\b",
     0, "high"),
    ("openai_key",
     r"\bsk-(?:proj-)?[A-Za-z0-9]{20,}\b",
     0, "critical"),
    ("anthropic_key",
     r"\bsk-ant-[A-Za-z0-9-]{20,}\b",
     0, "critical"),
    ("nvidia_key",
     r"\bnvapi-[A-Za-z0-9_-]{16,}\b",
     0, "critical"),
    ("age_secret_key",
     r"\bAGE-SECRET-KEY-1[0-9A-Z]{58}\b",
     0, "critical"),
    ("generic_secret_assign",
     r"(?i)\b(password|passwd|pwd|secret|api[_-]?key|apikey"
     r"|auth[_-]?token|access[_-]?token|client[_-]?secret"
     r"|db[_-]?pass(?:word)?|token)\b"
     r"\s*[:=]\s*['\"]?([^'\"\s#,;]{8,})['\"]?",
     2, "medium"),
    ("connection_string",
     r"(?i)\b(postgres(?:ql)?|mysql|mariadb|mongodb(?:\+srv)?"
     r"|redis(?:s)?|amqp(?:s)?|clickhouse)://([^:/\s@]+):([^@/\s]+)@",
     3, "high"),
]
PATTERNS = [(n, re.compile(rx), g, s) for n, rx, g, s in _RAW]

_PLACEHOLDERS = {
    "example", "changeme", "password", "12345678", "qwerty",
    "placeholder", "sample", "test", "demo", "fake", "none",
    "null", "undefined", "todo", "xxx",
}
_PLACEHOLDER_SUBSTR = (
    "example", "placeholder", "changeme", "your_", "_here",
    "xxx", "***", "<", ">",
)


def is_placeholder(value):
    v = value.strip().strip("'\"").lower()
    if v in _PLACEHOLDERS:
        return True
    if len(set(v)) <= 2:
        return True
    return any(s in v for s in _PLACEHOLDER_SUBSTR)


def shannon(s):
    if not s:
        return 0.0
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in Counter(s).values())


_ENTROPY_RE = re.compile(r"[A-Za-z0-9_+/=.$-]{24,}")
_ENTROPY_MIN = 4.6


def entropy_tokens(text):
    for m in _ENTROPY_RE.finditer(text):
        tok = m.group(0).strip(".-=$")
        if len(tok) < 24:
            continue
        if "/" in tok and "." in tok:
            continue
        if tok.count("-") > 6:
            continue
        if shannon(tok) >= _ENTROPY_MIN:
            yield tok, m.start()


def redact(value):
    if not value or len(value) <= 10:
        return "***"
    return value[:4] + chr(8230) + value[-2:]


def fingerprint(pattern, value):
    h = hashlib.sha256(("%s:%s" % (pattern, value)).encode()).hexdigest()[:16]
    return "sha256:" + h


def scan_text(text):
    out = []
    used = []
    for name, rx, grp, sev in PATTERNS:
        for m in rx.finditer(text):
            val = m.group(grp) if grp else m.group(0)
            if not val:
                continue
            span = (m.start(), m.end())
            if any(a < span[1] and span[0] < b for a, b in used):
                continue
            used.append(span)
            line = text.count("\n", 0, m.start()) + 1
            out.append({"line": line, "pattern": name, "severity": sev,
                        "value": val, "placeholder": bool(is_placeholder(val))})
    for tok, start in entropy_tokens(text):
        if any(a < start + len(tok) and start < b for a, b in used):
            continue
        line = text.count("\n", 0, start) + 1
        out.append({"line": line, "pattern": "high_entropy",
                    "severity": "low", "value": tok,
                    "placeholder": bool(is_placeholder(tok))})
    return out


def git(repo, *argv, raw=False):
    r = subprocess.run(["git", "-C", repo] + list(argv),
                       capture_output=True, text=not raw)
    return r.stdout


STORE_SUBS = [".env", "token", "secret", "credential",
              ".pem", ".key", ".p12", ".pfx", "passwd", "password"]


def sweep(repo):
    # all objects reachable from history; keep blobs only (batch, fast)
    objs = git(repo, "rev-list", "--all", "--objects").splitlines()
    shas = [l.split(" ", 1)[0] for l in objs if l.strip()]
    # map blob -> paths (types resolved in bulk below)
    p = subprocess.run(["git", "-C", repo, "cat-file", "--batch-check"],
                       input="\n".join(shas).encode(), capture_output=True)
    blob_shas = set()
    for line in p.stdout.decode(errors="replace").splitlines():
        parts = line.split(" ")
        if len(parts) >= 2 and parts[1] == "blob":
            blob_shas.add(parts[0])
    # map blob -> paths
    blob_paths = {}
    for line in objs:
        parts = line.split(" ", 1)
        if len(parts) == 2 and parts[0] in blob_shas:
            blob_paths.setdefault(parts[0], set()).add(parts[1])
    findings = []
    scanned = 0
    for blob, paths in blob_paths.items():
        data = git(repo, "cat-file", "-p", blob, raw=True)
        if b"\x00" in data[:8192] or len(data) > 2000000:
            continue
        text = data.decode("utf-8", errors="replace")
        scanned += 1
        rel = sorted(paths)[0]
        for f in scan_text(text):
            val = f["value"]
            if len(val) > 4000:
                continue
            findings.append({
                "blob": blob, "path": rel, "paths": sorted(paths),
                "line": f["line"], "pattern": f["pattern"],
                "severity": f["severity"],
                "redacted": redact(val),
                "fingerprint": fingerprint(f["pattern"], val),
                "placeholder": f["placeholder"], "_raw": val,
            })
    seen, uniq = set(), []
    for f in findings:
        k = (f["fingerprint"], f["blob"])
        if k not in seen:
            seen.add(k)
            uniq.append(f)
    for f in uniq:  # attribute introducing commits via -S (stays on host)
        out = git(repo, "log", "--all", "--format=%H|%ci|%s",
                  "-S", f["_raw"], "--", f["path"])
        commits = []
        for line in out.splitlines():
            pr = line.split("|", 2)
            if len(pr) == 3:
                commits.append({"sha": pr[0][:12], "date": pr[1],
                                "subject": pr[2][:100]})
        f["commits"] = commits
        del f["_raw"]
    tracked = git(repo, "ls-files").splitlines()
    store_files = [t for t in tracked
                   if any(s in os.path.basename(t).lower() for s in STORE_SUBS)]
    branches = git(repo, "branch", "-a", "--format=%(refname:short)").splitlines()
    ncommits = git(repo, "rev-list", "--all", "--count").strip()
    return {"branches": branches, "commit_count": ncommits,
            "blobs_scanned": scanned, "blobs_total": len(blob_paths),
            "findings": uniq, "tracked_store_like_files": store_files}


def main():
    out = {}
    for repo in sys.argv[1:]:
        try:
            out[repo] = sweep(repo)
        except Exception as e:
            out[repo] = {"error": str(e)[:200]}
    json.dump(out, sys.stdout, indent=1)
    sys.stdout.write("\n")


main()
