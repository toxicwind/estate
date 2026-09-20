#!/usr/bin/env python3
"""bidder_smoke.py -- MINIMAL test bidder for auctioneer e2e.

NOT the real bidder implementation (t2-impl-bidder owns that). This just
posts signed BID / RESULT / HEARTBEAT wire messages so the auctioneer can
be tested end to end.

Usage:
    bidder_smoke.py --task-id T --attempt N --bidder bidder-a \\
        --confidence 0.8 --cost 50 --eta-s 120 [--capabilities shell,text]
    bidder_smoke.py --task-id T --attempt N --bidder bidder-a \\
        --result done --quality 0.9 --summary "did the thing"
    bidder_smoke.py --task-id T --attempt N --bidder bidder-a --heartbeat
"""
import argparse
import sys
import time
from pathlib import Path

BASE = Path("/home/toxic/sovereign/killer-features/bid-market")
sys.path.insert(0, str(BASE))
import market as M


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-id", required=True)
    ap.add_argument("--attempt", type=int, default=1)
    ap.add_argument("--bidder", required=True)
    ap.add_argument("--confidence", type=float, default=0.8)
    ap.add_argument("--cost", type=float, default=50.0)
    ap.add_argument("--eta-s", type=float, default=120.0)
    ap.add_argument("--capabilities", default="shell,text")
    ap.add_argument("--result", choices=("done", "failed"), default=None)
    ap.add_argument("--quality", type=float, default=1.0)
    ap.add_argument("--summary", default="")
    ap.add_argument("--heartbeat", action="store_true")
    args = ap.parse_args()

    M.ensure_key(args.bidder)
    if args.heartbeat:
        human = f"HEARTBEAT {args.task_id} from {args.bidder}"
        payload = {"task_id": args.task_id, "attempt": args.attempt,
                   "bidder": args.bidder, "ts": time.time()}
        mt, title = "HEARTBEAT", f"hb-{args.task_id}"
    elif args.result:
        human = (f"RESULT {args.task_id}: {args.result} by {args.bidder}\n\n"
                 f"{args.summary}")
        payload = {"task_id": args.task_id, "attempt": args.attempt,
                   "bidder": args.bidder, "status": args.result,
                   "quality": args.quality, "summary": args.summary,
                   "posted_ts": time.time()}
        mt, title = "RESULT", f"result-{args.task_id}"
    else:
        human = (f"BID {args.task_id} from {args.bidder}: "
                 f"conf={args.confidence} cost={args.cost} eta={args.eta_s}s")
        payload = {"task_id": args.task_id, "attempt": args.attempt,
                   "bidder": args.bidder, "confidence": args.confidence,
                   "cost": args.cost, "eta_s": args.eta_s,
                   "capabilities": args.capabilities.split(","),
                   "posted_ts": time.time()}
        mt, title = "BID", f"bid-{args.task_id}-{args.bidder}"
    seq, fname = M.post_wire(M.CHANNEL, args.bidder, title, human,
                             payload, mt)
    print(f"posted {mt} seq={seq} file={fname}")


if __name__ == "__main__":
    main()
