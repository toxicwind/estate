"""The REAL bidder pool (mirrors killer-features/bid-market/profiles.py).

Market pool: 5 real bidder.py processes —
  bidder-flash, bidder-flash-2, bidder-mule, bidder-specialist,
  bidder-specialist-2

For the naive baseline ("same bidder pool, dumber allocation"), worker
params are derived from the real profiles:
  caps      <- {shell,python} kinds intersected with profile caps
  delay_s   <- cost_bias * 1.0s  (same relative speeds as the market)
  fail_rate <- 0

Oracle (ground-truth best-suited, from the market's own model):
  best = max capability_match, tie -> min cost_bias
  shell-text  -> flash       (full match, cheapest)
  shell-file  -> flash       (1/2 match, cheapest of the 1/2s)
  python-compute -> specialist (1/2 match, cheaper than mule)
  python-data -> specialist   (full match)
"""

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load_bidder_profiles():
    # Load the teammate's profiles.py by path (NOT by module name: e2e/
    # has its own profiles.py and sys.modules would collide).
    loc = HERE.parent / "profiles.py"
    spec = importlib.util.spec_from_file_location("bidder_profiles", loc)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


bidder_profiles = _load_bidder_profiles()

# (worker_name, profile_name) for the 5 market processes
POOL = [("flash-1", "flash"), ("flash-2", "flash"), ("mule-1", "mule"),
        ("specialist-1", "specialist"), ("specialist-2", "specialist")]

KINDS = {"shell", "python"}


def worker_params(profile_name):
    p = bidder_profiles.get(profile_name)
    return {"caps": KINDS & set(p["caps"]),
            "delay_s": float(p["cost_bias"]) * 1.0,
            "fail_rate": 0.0}


def worker_params_by_name(worker_name):
    for w, prof in POOL:
        if w == worker_name:
            return worker_params(prof)
    raise KeyError(worker_name)


ORACLE_CATEGORY = {"shell-text": "flash", "shell-file": "flash",
                   "python-compute": "specialist", "python-data": "specialist"}


def oracle_best(task):
    """Ground-truth best-suited PROFILE for allocation-quality scoring."""
    return ORACLE_CATEGORY[task["category"]]


def profile_of_bidder(bidder_id):
    """bidder-flash-2 -> flash ; bidder-mule -> mule ; flash-1 -> flash."""
    s = bidder_id
    if s.startswith("bidder-"):
        s = s[len("bidder-"):]
    parts = s.split("-")
    if parts[-1].isdigit():
        parts = parts[:-1]
    return "-".join(parts)


def is_oracle_win(task, bidder_id):
    return profile_of_bidder(bidder_id) == oracle_best(task)
