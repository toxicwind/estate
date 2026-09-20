#!/usr/bin/env python3
"""Similarity audit for the 93 'different' files: stash@{2} blob vs worktree."""
import os, subprocess, json
from difflib import SequenceMatcher

ROOT = "/home/toxic/sovereign"
r = json.load(open("/home/toxic/stash-merge-20260914/stash2-audit.json"))
paths = r["different"]

# batch-fetch stash blobs
req = "".join(f"stash@{{2}}:{p}\n" for p in paths)
p = subprocess.run(["git", "cat-file", "--batch"], cwd=ROOT,
                   input=req.encode(), capture_output=True)
out, blobs, pos = p.stdout, {}, 0
for path in paths:
    nl = out.index(b"\n", pos)
    parts = out[pos:nl].decode().split()
    pos = nl + 1
    if len(parts) >= 3 and parts[1] != "missing":
        size = int(parts[2])
        blobs[path] = out[pos:pos + size]
        pos += size + 1

rows = []
for path in paths:
    full = os.path.join(ROOT, path)
    try:
        with open(full, "rb") as f:
            tree = f.read()
    except OSError:
        rows.append((path, "unreadable-tree", 0, 0, 0))
        continue
    blob = blobs.get(path)
    if blob is None:
        rows.append((path, "no-blob", 0, 0, 0))
        continue
    try:
        t1, t2 = tree.decode("utf-8", "replace"), blob.decode("utf-8", "replace")
        ratio = SequenceMatcher(None, t1, t2).ratio()
        rows.append((path, "ok", ratio, len(tree), len(blob)))
    except Exception:
        rows.append((path, "binary?", 1.0 if tree == blob else 0.0, len(tree), len(blob)))

rows.sort(key=lambda x: x[2])
print(f"{'ratio':>6} {'tree':>9} {'stash':>9}  path")
for path, st, ratio, ts, bs in rows:
    flag = ""
    if st != "ok":
        flag = f" [{st}]"
    elif ratio > 0.95:
        flag = "  ~trivial"
    elif ts == 0 or bs == 0:
        flag = "  EMPTY-SIDE"
    print(f"{ratio:6.3f} {ts:9d} {bs:9d}  {path}{flag}")

json.dump([{"path": p, "status": s, "ratio": r_, "tree_size": t, "stash_size": b}
           for p, s, r_, t, b in rows],
          open("/home/toxic/stash-merge-20260914/stash2-similarity.json", "w"), indent=1)
