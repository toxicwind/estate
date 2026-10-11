#!/usr/bin/env python3
import json, hashlib, sys
from collections import Counter
storms = set(sys.argv[1].split(","))
outp = sys.argv[2]
turns = []
for path in sys.argv[3:]:
    for line in open(path, encoding="utf-8", errors="replace"):
        try: o = json.loads(line)
        except: continue
        if o.get("type") != "item": continue
        it = o.get("item") or {}
        if it.get("type") != "message": continue
        tx = it.get("text") or ""
        if tx: turns.append({"role": it.get("role"), "md5": hashlib.md5(tx.encode()).hexdigest(), "len": len(tx)})
for t in turns: t["label"] = -1 if t["md5"] in storms else 0
md5s = [t["md5"] for t in turns]
for i, t in enumerate(turns):
    if t["label"] == -1:
        t["echo_chain"] = any(m in storms for m in md5s[max(0, i-5):i])
json.dump(turns, open(outp, "w"))
print(f"wrote {outp}: {len(turns)} turns, {sum(1 for t in turns if t['label']==-1)} storm")
