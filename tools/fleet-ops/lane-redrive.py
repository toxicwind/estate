#!/usr/bin/env python3
"""lane-redrive: deterministic dirty-state reactor for the lane pollers.

The lane pollers are report-only by design ("Never re-drive other lanes'
work"). This engine closes the loop: it consumes the pollers' run ledger,
dedupes dirty items by watermark, and escalates NEW or CHANGED dirty state
as page records. Unchanged dirty state stays quiet.

Pipeline:
  run-ledger.jsonl (poller output, now includes the full "dirty" item list)
    -> lane-redrive.py (this file): classify, watermark, emit page records
    -> ~/workspace/state/lane-redrive.pages.jsonl (append-only outbox)
    -> fleet-watchdog driver.sh syncs it to awrawr-pc
    -> sweep.py relays unposted pages to the fleet room (watermarked)

Item key: "<lane>:<debate_id>:<reason_class>". A page fires when:
  - the key is unseen (new dirty state), or
  - the detail changed since the last escalation AND at least
    RE_ESCALATE_S (1h) has passed (changed dirty state, rate-limited).

Reason classes are derived from the poller's dirty strings:
  direct-order, award, ownership-lost, bidding, events-grew, interrupt,
  contributor, owned-stale, heartbeat-due, unknown.

INVARIANTS:
  - Never spawns agents, never kills, never marks work failed.
  - Never fabricates: only poller-reported items become pages.
  - --dry-run prints what would be paged without writing anything.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

HOME = os.path.expanduser("~")
STATE_DIR = os.path.join(HOME, "workspace", "fleet-ping")
RUN_LEDGER = os.path.join(STATE_DIR, "run-ledger.jsonl")
WATERMARK = os.path.join(STATE_DIR, "lane-redrive-watermark.json")
PAGES_OUT = os.path.join(HOME, "workspace", "state", "lane-redrive.pages.jsonl")
RE_ESCALATE_S = 3600
TAIL_LINES = 600

REASON_RULES = [
    ("DIRECT ORDER", "direct-order"),
    ("AWARD landed", "award"),
    ("no longer owned", "ownership-lost"),
    ("bidding re-opened", "bidding"),
    ("bidding round", "bidding"),
    ("events (was", "events-grew"),
    ("INTERRUPT", "interrupt"),
    ("contributor activity", "contributor"),
    ("STALE", "owned-stale"),
    ("heartbeat due", "heartbeat-due"),
]


def iso_now():
    return datetime.now(timezone.utc).isoformat()


def classify(item):
    for needle, cls in REASON_RULES:
        if needle in item:
            return cls
    return "unknown"


def debate_of(item):
    return item.split(":", 1)[0].strip()[:16]


def load_watermark():
    try:
        with open(WATERMARK) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def latest_runs():
    """Latest ok run record per lane from the run ledger tail."""
    runs = {}
    try:
        with open(RUN_LEDGER) as f:
            lines = f.readlines()[-TAIL_LINES:]
    except OSError:
        return runs
    for line in lines:
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if not r.get("ok"):
            continue
        lane = r.get("lane")
        if lane:
            runs[lane] = r  # ledger is chronological; last wins
    return runs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    now = iso_now()
    wm = load_watermark()
    runs = latest_runs()

    pages = []
    for lane in sorted(runs):
        rec = runs[lane]
        for item in rec.get("dirty") or []:
            did = debate_of(item)
            cls = classify(item)
            key = f"{lane}:{did}:{cls}"
            prev = wm.get(key)
            detail = item[len(did):].lstrip(": ").strip()[:200]
            if prev is None:
                fire, why = True, "new"
            else:
                age = (datetime.now(timezone.utc)
                       - datetime.fromisoformat(prev["last_escalated"])).total_seconds()
                if prev.get("last_detail") != detail and age >= RE_ESCALATE_S:
                    fire, why = True, "changed"
                else:
                    fire, why = False, "unchanged"
            entry = {"first_seen": (prev or {}).get("first_seen", now),
                     "last_detail": detail,
                     "n": (prev or {}).get("n", 0) + 1,
                     "last_escalated": (now if fire else prev["last_escalated"])
                     if prev else now}
            wm[key] = entry
            if fire:
                pages.append({
                    "ts": now,
                    "kind": "lane_redrive_page",
                    "lane": lane,
                    "debate_id": did,
                    "reason": cls,
                    "detail": detail,
                    "why": why,
                })

    result = {"ok": True, "lanes_seen": sorted(runs),
              "dirty_items": sum(len((runs[l].get("dirty") or []))
                                 for l in runs),
              "pages": len(pages), "dry_run": args.dry_run}

    if args.dry_run:
        result["would_page"] = pages
        print(json.dumps(result, indent=1))
        return 0

    if pages:
        os.makedirs(os.path.dirname(PAGES_OUT), exist_ok=True)
        with open(PAGES_OUT, "a") as f:
            for p in pages:
                f.write(json.dumps(p) + "\n")
    with open(WATERMARK, "w") as f:
        json.dump(wm, f, indent=1)
    result["paged"] = [
        f"{p['lane']}/{p['debate_id']}:{p['reason']}" for p in pages]
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
