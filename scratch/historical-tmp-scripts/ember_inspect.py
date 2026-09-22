import json, glob, os
for ch in ("fleet", "bid-market"):
    d = f"/home/toxic/.shingle/squawk-root/{ch}"
    try:
        files = sorted(os.listdir(d))[-6:]
    except Exception as e:
        print(ch, "ERR", e); continue
    print("###", ch, files)
    f = os.path.join(d, files[-1])
    try:
        with open(f) as fh: raw = fh.read()
    except Exception as e:
        print("read err", e); continue
    print("len", len(raw))
    print(raw[:800])
    print("----")
