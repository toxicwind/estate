#!/usr/bin/env python3
"""heartbeat-suspicion.py -- READ-ONLY lane heartbeat staleness reporter.

Reads every coord/lanes/*.json, derives the age of its "heartbeat" field,
and classifies the lane as alive / suspect / stale per the thresholds in
coord/lanes/HEARTBEAT-THRESHOLDS.md. Prints a report to stdout.

Writes nothing. Touches no state. Safe to run from any poll cron or ad hoc.

Theory: simplified accrual suspicion (cf. Hayashibara et al. 2004, phi accrual;
Satzger et al. 2007, adaptive accrual). Suspicion accrues only after
ACCEPTABLE_PAUSE of silence, grows with age/interval, and is floored so
metronomic lanes do not flag on a single late cron (cf. Akka
min-std-deviation floor).
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

LANES_DIR = Path("/home/toxic/sovereign/hatch/agents/ember/coord/lanes")

EXPECTED_INTERVAL = 180.0   # seconds: 3-minute poll crons
ACCEPTABLE_PAUSE = EXPECTED_INTERVAL      # grace before suspicion accrues
SUSPECT_AFTER = 2 * EXPECTED_INTERVAL     # 12 min: suspect
STALE_AFTER = 10 * EXPECTED_INTERVAL      # 30 min: stale, escalate


def parse_hb(value):
    """Parse a lane heartbeat value into epoch seconds. None if unparsable."""
    if not value:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(text).timestamp()
        except ValueError:
            return None
    return None


def suspicion(age, interval=EXPECTED_INTERVAL):
    """Simplified accrual suspicion in [0, +inf). 0 below the pause floor."""
    if age < ACCEPTABLE_PAUSE:
        return 0.0
    return age / interval - 1.0


def classify(age):
    if age < SUSPECT_AFTER:
        return "alive"
    if age < STALE_AFTER:
        return "suspect"
    return "stale"


def reason(age, hb_epoch, files_ok):
    if not files_ok:
        return "bridge_unreachable"
    if hb_epoch is None:
        return "no_heartbeat_field"
    if age < SUSPECT_AFTER:
        return "ok"
    return "heartbeat_timeout"


def main():
    now = time.time()
    rows = []
    files = sorted(LANES_DIR.glob("*.json"))
    if not files:
        print("no lane files found at %s" % LANES_DIR, file=sys.stderr)
        return 2
    for path in files:
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            rows.append((path.name, "unknown", -1, 0.0, "unreadable"))
            continue
        hb_epoch = parse_hb(data.get("heartbeat"))
        if hb_epoch is None:
            hb_epoch = parse_hb(data.get("heartbeat_ts"))
        if hb_epoch is None:
            rows.append((path.name, "unknown", -1, 0.0,
                         "no_heartbeat_field"))
            continue
        age = now - hb_epoch
        if age < 0:
            rows.append((path.name, "alive", 0, 0.0, "future_timestamp"))
            continue
        rows.append((path.name, classify(age), age, suspicion(age),
                     reason(age, hb_epoch, True)))
    print("%-34s %-8s %10s %8s %s" % ("lane", "status", "age", "suspicion", "reason"))
    for name, status, age, susp, rsn in rows:
        age_s = ("%.0fs" % age) if age >= 0 else "n/a"
        print("%-34s %-8s %10s %8.2f %s" % (name, status, age_s, susp, rsn))
    stale = [r for r in rows if r[1] in ("suspect", "stale")]
    print("\n%d lanes checked, %d suspect-or-stale" % (len(rows), len(stale)))
    return 1 if any(r[1] == "stale" for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
