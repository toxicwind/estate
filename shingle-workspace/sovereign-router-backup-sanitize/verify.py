#!/usr/bin/env python3
"""Verify sanitized sovereign-router-backup: ref target, metadata parity, no token paths."""
import json, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from gh import gh

REPO = "toxicwind/sovereign-router-backup"
state = json.load(open("state.json"))
meta = json.load(open("meta_oldest_first.json"))
new_head = state["new_head"]
ok = True

# 1. main points at new head
st, ref = gh("GET", f"/repos/{REPO}/git/refs/heads/main")
assert st == 200, st
print("main now:", ref["object"]["sha"][:12], "| matches new_head:", ref["object"]["sha"] == new_head)

# 2. per-commit metadata parity (single commit expected)
m = meta[0]
st, nc = gh("GET", f"/repos/{REPO}/git/commits/{new_head}")
assert st == 200, st
checks = {
    "message": nc["message"] == m["message"],
    "author_name": nc["author"]["name"] == m["author"]["name"],
    "author_email": nc["author"]["email"] == m["author"]["email"],
    "author_date": nc["author"]["date"] == m["author"]["date"],
    "committer_name": nc["committer"]["name"] == m["committer"]["name"],
    "committer_email": nc["committer"]["email"] == m["committer"]["email"],
    "committer_date": nc["committer"]["date"] == m["committer"]["date"],
    "parents_root": nc["parents"] == [],
}
for k, v in checks.items():
    print(f"  parity {k}: {v}")
    ok = ok and v

# 3. token paths gone from new tree
st, t = gh("GET", f"/repos/{REPO}/git/trees/{nc['tree']['sha']}?recursive=1")
assert st == 200, st
paths = [e["path"] for e in t.get("tree", [])]
hits = [p for p in paths if "kimi_tokens" in p]
print("paths containing kimi_tokens in new tree:", hits or "NONE")
ok = ok and not hits

# 4. old head still retrievable as dangling object (expected; not deleted)
st, _ = gh("GET", f"/repos/{REPO}/git/commits/{state['old_head']}")
print("old head still addressable via API (dangling, not referenced by any ref):", st == 200)

# 5. confirm new tree differs from old only by dropped files
st, ot = gh("GET", f"/repos/{REPO}/git/trees/{m['tree']}?recursive=1")
opaths = {e["path"] for e in ot.get("tree", [])}
npaths = set(paths)
print("old tree entry count:", len(opaths), "| new tree entry count:", len(npaths))
print("dropped exactly the two token files:", opaths - npaths == {"ultimate_extract/kimi_tokens.json", "ultimate_extract/kimi_tokens_full.json"})

print("VERIFICATION", "PASS" if ok else "FAIL")
