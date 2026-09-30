import json, glob, os
out = {}
for ch in ("fleet", "bid-market"):
    files = sorted(glob.glob(f"/home/toxic/.shingle/squawk-root/{ch}/*"))
    msgs = []
    for f in files:
        try:
            with open(f) as fh: d = json.load(fh)
        except Exception:
            continue
        msgs.append(d)
    msgs.sort(key=lambda m: m.get("seq", 0))
    out[ch] = [{"seq": m.get("seq"), "frm": m.get("frm"),
                "txt": str(m.get("txt", ""))[:220]} for m in msgs[-15:]]
print(json.dumps(out, indent=1))
