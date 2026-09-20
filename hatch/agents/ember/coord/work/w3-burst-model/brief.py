#!/usr/bin/env python3
"""w3-burst-model: model storm inter-arrival bursts; build a dedup sketch.
Plan: (1) load seed_list_chat.json; (2) compute per-digest inter-arrival gaps
from storm turn timestamps; (3) sketch: collapse same-md5 storm turns within a
30s window into one representative; (4) report collapse % and gap stats;
(5) RESULT.json.
"""
import json, os, time
from datetime import datetime, timezone

WORK = os.path.dirname(os.path.abspath(__file__))
SEEDS = "/home/toxic/.shingle/coord/work/seeds"

turns = json.load(open(os.path.join(SEEDS, "seed_list_chat.json")))
storm = [t for t in turns if t["label"] == -1]

def ts(t):
    return datetime.fromisoformat(t["ts"]).astimezone(timezone.utc).timestamp()

by_md5 = {}
for t in storm:
    by_md5.setdefault(t["md5"], []).append(ts(t))

def pct(xs, p):
    xs = sorted(xs)
    return xs[int(p * (len(xs) - 1))] if xs else 0

gap_stats, collapsed_total, kept_total = {}, 0, 0
for md5, tss in by_md5.items():
    tss.sort()
    gaps = [b - a for a, b in zip(tss, tss[1:])]
    # dedup sketch: 30s same-md5 window -> one representative
    kept, last = 0, -1e18
    for x in tss:
        if x - last > 30:
            kept += 1
            last = x
    collapsed_total += len(tss) - kept
    kept_total += kept
    gap_stats[md5[:8]] = {"n": len(tss), "median_gap_s": round(pct(gaps, 0.5), 2),
                          "p10_gap_s": round(pct(gaps, 0.1), 2),
                          "p90_gap_s": round(pct(gaps, 0.9), 2)}

collapse_pct = round(100 * collapsed_total / max(1, collapsed_total + kept_total), 1)
r = {"lane": "w3-burst-model",
     "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
     "claims": [f"30s same-digest dedup sketch collapses {collapse_pct}% of storm turns",
                "burst gaps are machine-speed: see gap_stats"],
     "evidence": {"gap_stats": gap_stats,
                  "storm_turns": collapsed_total + kept_total,
                  "collapsed": collapsed_total, "kept": kept_total,
                  "collapse_pct": collapse_pct},
     "proof_files": ["brief.py"]}
json.dump(r, open(os.path.join(WORK, "RESULT.json"), "w"), indent=1)
print(json.dumps(r, indent=1))
