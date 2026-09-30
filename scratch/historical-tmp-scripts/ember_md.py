import json, glob, os, re
for ch in ("fleet", "bid-market"):
    d = f"/home/toxic/.shingle/squawk-root/{ch}"
    mds = sorted(glob.glob(os.path.join(d, "*.md")))
    print("===", ch, "md count", len(mds))
    for f in mds[-6:]:
        base = os.path.basename(f)
        m = re.match(r"(\d+)-", base)
        seq = int(m.group(1)) if m else None
        with open(f) as fh: txt = fh.read()
        print("seq", seq, base, "|", txt[:260].replace("\n", " "))
    print()
