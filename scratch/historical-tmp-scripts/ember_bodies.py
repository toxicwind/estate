import os, glob, re
jobs = [
  ("/home/toxic/.shingle/squawk-root/fleet", [12993,12994,12995,12996]),
  ("/home/toxic/.shingle/squawk-root/bid-market", [100329,100330,100331]),
]
for d, seqs in jobs:
    for s in seqs:
        hits = glob.glob(os.path.join(d, f"{s}-*.md"))
        for h in hits:
            with open(h) as fh: t = fh.read()
            print("===", os.path.basename(h))
            print(t[:900])
            print()
