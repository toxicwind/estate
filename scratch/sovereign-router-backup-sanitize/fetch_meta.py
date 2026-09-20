#!/usr/bin/env python3
"""Enumerate main commits of toxicwind/sovereign-router-backup, build meta_oldest_first.json."""
import json, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from gh import gh

REPO = "toxicwind/sovereign-router-backup"
# resolve main
st, ref = gh("GET", f"/repos/{REPO}/git/refs/heads/main")
assert st == 200, st
old_head = ref["object"]["sha"]
print("old head:", old_head, flush=True)

# walk commit chain oldest-first via parents (linear history expected)
chain = []
seen = set()
cur = old_head
while cur and cur not in seen:
    st, c = gh("GET", f"/repos/{REPO}/git/commits/{cur}")
    assert st == 200, (st, cur)
    seen.add(cur)
    chain.append(c)
    ps = [p["sha"] for p in c["parents"]]
    cur = ps[0] if ps else None
chain.reverse()
print("commit count:", len(chain), flush=True)
json.dump([c["sha"] for c in chain], open("commits.json", "w"), indent=1)
meta = [{"sha": c["sha"], "tree": c["tree"]["sha"], "message": c["message"],
         "author": {"name": c["author"]["name"], "email": c["author"]["email"], "date": c["author"]["date"]},
         "committer": {"name": c["committer"]["name"], "email": c["committer"]["email"], "date": c["committer"]["date"]}}
        for c in chain]
json.dump(meta, open("meta_oldest_first.json", "w"), indent=1)

# confirm token files present in HEAD tree (paths only, no content)
DROP = ["ultimate_extract/kimi_tokens.json", "ultimate_extract/kimi_tokens_full.json"]
st, t = gh("GET", f"/repos/{REPO}/git/trees/{chain[-1]['tree']['sha']}?recursive=1")
assert st == 200, st
paths = {e["path"] for e in t.get("tree", [])}
for p in DROP:
    print(f"HEAD tree contains {p}: {p in paths}", flush=True)
print("DONE", flush=True)
