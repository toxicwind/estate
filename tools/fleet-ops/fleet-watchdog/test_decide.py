#!/usr/bin/env python3
"""Transition tests for the fleet-watchdog v2 paging brain (decide()) plus
the manifest-driven block checker (check_blocks / build_expected_map).

Synthetic observations only — no server, no fleet room. Run on awrawr-pc:
  python3 test_decide.py
Exit 0 = all PASS, 1 = failure. This is the post-use verification of the
paging logic: degradation pages, recovery pages, silence on steady state,
and the blind-spot fix (a lane whose whole block vanishes from the mirror
is still expected via lane_manifest.json).
"""
import importlib.util
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

spec = importlib.util.spec_from_file_location(
    "sweep", "/home/toxic/sovereign/tools/fleet-ops/fleet-watchdog/sweep.py")
sweep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sweep)

NOW = datetime(2026, 9, 19, 5, 30, 0, tzinfo=timezone.utc)


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def old_state(live_set, last_seen=None, last_sweep=NOW - timedelta(seconds=60),
              blocks=True):
    lanes = {}
    for n in range(1, 9):
        lanes[str(n)] = {
            "block": blocks, "live": n in live_set,
            "last_seen_ts": iso(last_seen[n]) if last_seen and n in last_seen else None,
            "last_transition": None, "last_transition_ts": None}
    return {"version": 2, "last_sweep_ts": iso(last_sweep), "lanes": lanes,
            "transitions": []}


def obs_state(live_set, hb=None, missing=None):
    return {"server_ts": NOW,
            "lanes": {n: {"live": n in live_set,
                          "last_heartbeat": iso(hb[n]) if hb and n in hb else None}
                      for n in range(1, 9)},
            "missing_blocks": missing if missing is not None else []}


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        sys.exit(1)


# 1. steady state: all live, no change -> silence
old = old_state(set(range(1, 9)), {n: NOW - timedelta(seconds=60) for n in range(1, 9)})
_, pages, _ = sweep.decide(old, obs_state(set(range(1, 9)), {n: NOW for n in range(1, 9)}))
check("steady-all-live silent", pages == [], f"pages={pages}")

# 2. degradation: lane-3 live -> stale, last seen 6h12m ago
seen = {n: NOW - timedelta(seconds=60) for n in range(1, 9)}
seen[3] = NOW - timedelta(hours=6, minutes=12)
old = old_state(set(range(1, 9)), seen)
new, pages, tr = sweep.decide(old, obs_state(set(range(1, 9)) - {3}))
check("degradation pages once", len(pages) == 1, f"pages={pages}")
check("degradation names lane-3", "lane-3 STALE" in pages[0], f"pages={pages}")
check("degradation carries age", "6h 12m" in pages[0], f"pages={pages}")
check("degradation transition logged", tr == [{"ts": iso(NOW), "lane": 3, "from": "live", "to": "stale"}], f"tr={tr}")
check("stale lane keeps last_seen", new["3"]["last_seen_ts"] == iso(seen[3]))

# 3. recovery: lane-3 stale -> live after 22m dark
old2 = old_state(set(range(1, 9)) - {3}, {3: NOW - timedelta(minutes=22)})
new, pages, tr = sweep.decide(old2, obs_state(set(range(1, 9)), {3: NOW}))
check("recovery pages once", len(pages) == 1, f"pages={pages}")
check("recovery names lane-3", "lane-3 LIVE again" in pages[0], f"pages={pages}")
check("recovery carries downtime", "22m" in pages[0], f"pages={pages}")
check("recovered lane last_seen refreshes", new["3"]["last_seen_ts"] == iso(NOW))

# 4. silence after recovery: same obs again -> no pages
old3 = {"version": 2, "last_sweep_ts": iso(NOW - timedelta(seconds=60)),
        "lanes": new, "transitions": []}
_, pages, _ = sweep.decide(old3, obs_state(set(range(1, 9)), {n: NOW for n in range(1, 9)}))
check("post-recovery steady silent", pages == [], f"pages={pages}")

# 5. block lost -> page; block restored -> page
old = old_state(set(range(1, 9)), blocks=True)
_, pages, _ = sweep.decide(old, obs_state(set(range(1, 9)), missing=[5]))
check("block lost pages", any("lane-5" in p and "MISSING" in p for p in pages), f"pages={pages}")
old = old_state(set(range(1, 9)), blocks=False)
_, pages, _ = sweep.decide(old, obs_state(set(range(1, 9)), missing=[]))
check("block restored pages", any("lane-5" in p and "restored" in p for p in pages), f"pages={pages}")

# 6. watchdog gap: last sweep 20m ago (> 2x60s) -> gap page
old = old_state(set(range(1, 9)), last_sweep=NOW - timedelta(minutes=20))
_, pages, _ = sweep.decide(old, obs_state(set(range(1, 9))))
check("gap pages", any("watchdog gap" in p and "20m" in p for p in pages), f"pages={pages}")

# 6b. no gap at healthy cadence: last sweep 45s ago -> no gap page
old = old_state(set(range(1, 9)), last_sweep=NOW - timedelta(seconds=45))
_, pages, _ = sweep.decide(old, obs_state(set(range(1, 9))))
check("no gap page at 45s cadence", not any("watchdog gap" in p for p in pages), f"pages={pages}")

# 7. first run: old=None -> builds lanes, no crash, no phantom pages
new, pages, _ = sweep.decide(None, obs_state({7}))
check("first run builds 8 lanes", len(new) == 8 and new["7"]["live"] is True)
check("first run decide emits no pages (main adds baseline)", pages == [], f"pages={pages}")

# 8. multi-lane degradation in one sweep -> one page per lane
old = old_state(set(range(1, 9)))
_, pages, _ = sweep.decide(old, obs_state({7, 8}))
check("six degradations -> six pages",
      len(pages) == 6 and any("lane-1 STALE" in p for p in pages)
      and any("lane-6 STALE" in p for p in pages), f"pages={pages}")

# 9. blind-spot fix: whole lane-5 block vanishes from the mirror text, but the
#    manifest still expects lane-5 -> check_blocks flags it, decide pages it.
man, man_err = sweep.load_manifest()
check("manifest loads", man is not None and len(man) == 8, f"err={man_err}")
full_mirror = open(sweep.ROLLOVER).read()
# Excise lane-5's whole section: headers are NOT in numeric order in the
# mirror, so cut from the Lane 5 header to the next header (or EOF).
headers = sorted((m.start(), int(m.group(1)))
                 for m in re.finditer(r"^### Lane (\d+)\s*$", full_mirror, re.M))
idx5 = next(i for i, (s, n) in enumerate(headers) if n == 5)
sec_start = headers[idx5][0]
sec_end = headers[idx5 + 1][0] if idx5 + 1 < len(headers) else len(full_mirror)
gutted = full_mirror[:sec_start] + full_mirror[sec_end:]
prefix5 = [p for p, n in man.items() if n == 5][0]
check("lane-5 header excised", re.search(r"^### Lane 5\s*$", gutted, re.M) is None)
check("lane-5 prefix gone from gutted mirror", prefix5 not in gutted)
missing = sweep.check_blocks(man, gutted)
check("gutted mirror flags lane-5 missing", missing == [5], f"missing={missing}")
check("full mirror flags nothing", sweep.check_blocks(man, full_mirror) == [])
# 9b. a bare mention of lane-5 elsewhere does NOT count as holding a block
mention = gutted + "\nnote: lane-5 was mentioned here in passing\n"
check("bare mention not a block", sweep.check_blocks(man, mention) == [5])
# 9c. end-to-end through decide: block loss pages
old = old_state(set(range(1, 9)), blocks=True)
_, pages, _ = sweep.decide(old, obs_state(set(range(1, 9)), missing=[5]))
check("blind-spot block loss pages", any("lane-5" in p and "MISSING" in p for p in pages), f"pages={pages}")

print("ALL TRANSITION + BLIND-SPOT SCENARIOS PASS")
