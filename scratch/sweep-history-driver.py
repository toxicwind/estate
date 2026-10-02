#!/usr/bin/env python3
"""History secrets sweep driver.

Runs on awrawr-pc next to secret-scanner's main.py/patterns.py.
For each repo: walks every blob reachable from --all history (covers renames,
since blobs are content-addressed), scans blob contents with the same
pattern library + redaction as the working-tree scanner, and attributes each
finding to the commit(s) that introduced the string via `git log -S`.

Also lists currently-tracked credential-bearing filenames.

Output: redacted JSON to stdout. Raw values never leave this host.
"""
import json
import os
import subprocess
import sys

import main as S
import patterns as P

STORE_NAME_RES = [
    ".env", ".env.", "token", "secret", "credential", "credentials",
    ".pem", ".key", ".p12", ".pfx", "passwd", "password",
]


def run(repo, *argv):
    r = subprocess.run(["git", "-C", repo] + list(argv),
                       capture_output=True, text=True, errors="replace")
    return r.stdout


def run_bytes(repo, *argv):
    r = subprocess.run(["git", "-C", repo] + list(argv), capture_output=True)
    return r.stdout


def blob_paths(repo):
    """All blobs reachable from history -> {blob_sha: set(paths)}."""
    out = run(repo, "rev-list", "--all", "--objects")
    blobs = {}
    for line in out.splitlines():
        line = line.strip()
        parts = line.split(" ", 1)
        if len(parts) != 2:
            continue
        sha, path = parts
        if run(repo, "cat-file", "-t", sha).strip() != "blob":
            continue
        blobs.setdefault(sha, set()).add(path)
    return blobs


def introducing_commits(repo, value, path):
    """Commits that changed the occurrence count of value in path (git -S)."""
    out = run(repo, "log", "--all", "--format=%H|%ci|%s", "-S", value,
              "--", path)
    res = []
    for line in out.splitlines():
        p = line.split("|", 2)
        if len(p) == 3:
            res.append({"sha": p[0], "date": p[1], "subject": p[2]})
    return res


def looks_like_store(name):
    n = name.lower()
    return any(s in n for s in STORE_NAME_RES)


def sweep_repo(repo):
    blobmap = blob_paths(repo)
    findings = []
    scanned = 0
    for blob, paths in blobmap.items():
        data = run_bytes(repo, "cat-file", "-p", blob)
        if b"\x00" in data[:8192] or len(data) > 2_000_000:
            continue
        text = data.decode("utf-8", errors="replace")
        scanned += 1
        rel = sorted(paths)[0]
        for f in S.scan_text(text, rel):
            val = f.get("value") or ""
            if not val or len(val) > 4000:
                continue
            findings.append({
                "blob": blob,
                "path_example": rel,
                "all_paths": sorted(paths),
                "pattern": f["pattern"],
                "severity": f["severity"],
                "line": f.get("line"),
                "redacted": S.redact(val),
                "fingerprint": S.fingerprint(f["pattern"], val),
                "placeholder": P.is_placeholder(val),
                "_raw": val,
            })
    # dedupe by fingerprint+blob
    seen, uniq = set(), []
    for f in findings:
        k = (f["fingerprint"], f["blob"])
        if k not in seen:
            seen.add(k)
            uniq.append(f)
    # attribute commits, then strip raw values
    for f in uniq:
        try:
            f["commits"] = introducing_commits(repo, f["_raw"], f["path_example"])
        except Exception:
            f["commits"] = []
        del f["_raw"]
    tracked = run(repo, "ls-files").splitlines()
    store_files = [t for t in tracked if looks_like_store(os.path.basename(t))]
    return {
        "blobs_scanned": scanned,
        "blobs_total": len(blobmap),
        "findings": uniq,
        "tracked_store_like_files": store_files,
    }


def main():
    out = {}
    for repo in sys.argv[1:]:
        out[repo] = sweep_repo(repo)
    json.dump(out, sys.stdout, indent=1)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
