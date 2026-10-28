"""Per-bidder local reputation + calibration (Agora-inspired).

reputation/<bidder_id>.json:
  {bids, assigns, successes, failures, total_duration_s, total_bid_latency_s,
   cal_mult}

score()      = Laplace-smoothed success rate, starts 0.5 (bid input).
cal_mult     = EMA of (actual_quality / predicted_confidence), init 1.0,
               clamped to [0.5, 1.5]. Multiplies raw confidence before
               bidding -- the bidder's self-calibration, mirroring the
               auctioneer's 0.85*cal+0.15*q rule from the other side.
"""

import json
import os
import tempfile
from pathlib import Path

REPUTATION_DIR = Path(__file__).resolve().parent / "reputation"


def _path(bidder_id):
    return REPUTATION_DIR / ("%s.json" % bidder_id)


def _base():
    return {"bids": 0, "assigns": 0, "successes": 0, "failures": 0,
            "total_duration_s": 0.0, "total_bid_latency_s": 0.0,
            "cal_mult": 1.0}


def load(bidder_id):
    rep = _base()
    p = _path(bidder_id)
    if p.exists():
        try:
            rep.update(json.loads(p.read_text()))
        except (ValueError, OSError):
            pass
    return rep


def save(bidder_id, rep):
    REPUTATION_DIR.mkdir(parents=True, exist_ok=True)
    p = _path(bidder_id)
    fd, tmp = tempfile.mkstemp(dir=str(REPUTATION_DIR), prefix=".tmp-")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(rep, f, indent=2)
            f.write("\n")
        os.replace(tmp, p)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def score(rep):
    a = rep.get("assigns", 0)
    s = rep.get("successes", 0)
    return (s + 2.0) / (a + 4.0)


def record_bid(bidder_id, latency_s):
    rep = load(bidder_id)
    rep["bids"] += 1
    rep["total_bid_latency_s"] += latency_s
    save(bidder_id, rep)
    return rep


def record_assign(bidder_id):
    rep = load(bidder_id)
    rep["assigns"] += 1
    save(bidder_id, rep)
    return rep


def record_result(bidder_id, predicted_confidence, success, duration_s):
    """Update counts + self-calibration. quality=1.0/0.0 for done/failed."""
    rep = load(bidder_id)
    if success:
        rep["successes"] += 1
    else:
        rep["failures"] += 1
    rep["total_duration_s"] += duration_s
    quality = 1.0 if success else 0.0
    pred = max(0.05, min(1.0, float(predicted_confidence or 0.5)))
    ratio = quality / pred  # >1 over-cautious, <1 over-confident
    old = float(rep.get("cal_mult", 1.0))
    rep["cal_mult"] = max(0.5, min(1.5, 0.85 * old + 0.15 * ratio))
    save(bidder_id, rep)
    return rep
