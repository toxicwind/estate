#!/usr/bin/env python3
"""Stash-vs-worktree overlap audit for stash@{2} in /home/toxic/sovereign."""
import os, subprocess, hashlib, json, sys

ROOT = "/home/toxic/sovereign"
OUT = "/home/toxic/stash-merge-20260914/stash2-audit.json"

def run(*a):
    return subprocess.run(a, cwd=ROOT, capture_output=True, text=True).stdout

def sha_of_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def batch_blob_shas(stash_ref, paths):
    """Fetch all blobs in one git cat-file --batch process. Returns {path: sha}."""
    import struct
    req = "".join(f"{stash_ref}:{p}\n" for p in paths)
    p = subprocess.run(["git", "cat-file", "--batch"],
                       cwd=ROOT, input=req.encode(), capture_output=True)
    out, result, pos = p.stdout, {}, 0
    for path in paths:
        nl = out.index(b"\n", pos)
        header = out[pos:nl].decode()
        pos = nl + 1
        parts = header.split()
        if len(parts) >= 3 and parts[1] != "missing":
            size = int(parts[2])
            h = hashlib.sha256(out[pos:pos + size]).hexdigest()
            result[path] = h
            pos += size + 1
    return result

def main():
    stash_ref = sys.argv[1] if len(sys.argv) > 1 else "stash@{2}"
    entries = []
    for line in run("git", "stash", "show", "--name-status", stash_ref).splitlines():
        if not line.strip():
            continue
        status, path = line.split("\t", 1)
        entries.append((status, path))

    # batch-fetch all stash blob hashes in one git process
    blob_shas = batch_blob_shas(stash_ref, [p for _, p in entries])

    missing, identical, different, skipped = [], [], [], []
    for status, path in entries:
        full = os.path.join(ROOT, path)
        if not os.path.lexists(full):
            missing.append(path)
            continue
        if os.path.isdir(full) and not os.path.islink(full):
            skipped.append(path + " [dir-in-tree]")
            continue
        try:
            tree_sha = sha_of_file(full)
        except OSError:
            skipped.append(path + " [unreadable]")
            continue
        blob_sha = blob_shas.get(path)
        if blob_sha is None:
            skipped.append(path + " [no-blob]")
        elif tree_sha == blob_sha:
            identical.append(path)
        else:
            different.append(path)

    report = {
        "stash": stash_ref,
        "total": len(entries),
        "missing": missing,
        "identical": identical,
        "different": different,
        "skipped": skipped,
        "counts": {
            "missing": len(missing),
            "identical": len(identical),
            "different": len(different),
            "skipped": len(skipped),
        },
    }
    with open(OUT, "w") as f:
        json.dump(report, f, indent=1)
    print(json.dumps(report["counts"]))
    # print first 30 of each non-empty bucket for the log
    for k in ("missing", "different", "skipped"):
        if report[k]:
            print(f"--- {k} (first 30) ---")
            for p in report[k][:30]:
                print(p)

if __name__ == "__main__":
    main()
