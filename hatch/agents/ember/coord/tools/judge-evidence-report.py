#!/usr/bin/env python3
"""judge-evidence-report.py -- READ-ONLY aggregator for the P4 judge
failure-evidence JSONL log.

Reads agents/oracle-market/work/judge-failure-evidence.jsonl (append-only,
one JSON object per failed judge attempt, written by _emit_failure_evidence
in agents/oracle-market/bin/oracle_ask.py) and prints, per provider:

  attempts, failures by error_class, p50/p95 latency_ms, last-failure age,
  trailing consecutive-failure run, and a one-line recommendation
  (e.g. "breaker would trip: N consecutive provider-class fails").

Writes nothing. Touches no state. Pure stdlib. Safe to run ad hoc or from a
read-only poll cron.

Usage:
  judge-evidence-report.py [--path LOG] [--since WHEN]

  --path   path to the JSONL log (default: the production path)
  --since  only rows with ts >= WHEN; ISO8601 (2026-09-22T04:00:00Z) or
           a duration suffix: 30m, 6h, 7d (measured back from now)
"""
import argparse
import json
import os
import sys
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEFAULT_PATH = "/home/toxic/sovereign/agents/oracle-market/work/judge-failure-evidence.jsonl"

# Mirror of the P1 breaker thresholds in oracle_ask.py (kept in sync by hand;
# the script reads them from env so a report can test hypothetical tuning).
ALLOWED_FAILS = int(os.environ.get("JUDGE_BREAKER_ALLOWED_FAILS", "3"))
COOLDOWN_S = float(os.environ.get("JUDGE_BREAKER_COOLDOWN_S", "300"))
HEDGE_DELAY_S = float(os.environ.get("JUDGE_HEDGE_DELAY_S", "40"))

# error classes the P1 breaker counts as provider-class failures
PROVIDER_CLASS = {
    "timeout", "http_5xx", "http_429", "http_402", "connection_error",
    "dns_failure", "tls_failure",
}


def parse_ts(value):
    """ISO8601 (with Z) -> epoch seconds. None if unparsable."""
    if not value:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text).timestamp()
    except ValueError:
        return None


def parse_since(raw):
    """ISO8601 or <n>m/h/d duration -> epoch seconds (or None for no filter)."""
    if raw is None:
        return None
    raw = raw.strip()
    if raw and raw[-1] in "mhd" and raw[:-1].replace(".", "", 1).isdigit():
        mult = {"m": 60, "h": 3600, "d": 86400}[raw[-1]]
        return time.time() - float(raw[:-1]) * mult
    ts = parse_ts(raw)
    if ts is None:
        raise SystemExit(f"error: cannot parse --since {raw!r} (ISO8601 or <n>m/h/d)")
    return ts


def percentile(sorted_vals, p):
    if not sorted_vals:
        return None
    idx = min(int(p * len(sorted_vals)), len(sorted_vals) - 1)
    return sorted_vals[idx]


def fmt_age(seconds):
    if seconds is None:
        return "n/a"
    if seconds < 0:
        seconds = 0
    if seconds < 60:
        return f"{int(seconds)}s"
    if seconds < 3600:
        return f"{seconds / 60:.1f}m"
    if seconds < 86400:
        return f"{seconds / 3600:.1f}h"
    return f"{seconds / 86400:.1f}d"


def recommend(name, st):
    """One-line verdict per provider."""
    if st["consec"] >= ALLOWED_FAILS:
        if name == "unknown":
            return (
                f"{st['consec']} consecutive provider-class fails but provider "
                f"is unattributable ('unknown' never trips the breaker)"
            )
        return (
            f"breaker would trip: {st['consec']} consecutive provider-class "
            f"fails >= ALLOWED_FAILS={ALLOWED_FAILS} (cooldown {COOLDOWN_S:.0f}s)"
        )
    if st["fails"]:
        classes = st["by_class"]
        if set(classes) <= {"timeout"}:
            p95 = st["p95"] or 0
            if p95 > HEDGE_DELAY_S * 1000:
                return (
                    f"timeout-only; p95 {p95:.0f}ms > hedge gate "
                    f"{HEDGE_DELAY_S:.0f}s: review HEDGE_DELAY_S"
                )
            return "timeout-only: hedge gate covers tail; no breaker action"
        if "parse_failure" in classes and len(classes) == 1:
            return "parse failures only (client-side): not provider-class; tune parser/prompts, no breaker action"
        return "mixed classes: watch; below breaker threshold"
    return "no failures in window"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--path", default=DEFAULT_PATH)
    ap.add_argument("--since", default=None,
                    help="ISO8601 or duration like 30m/6h/7d; default: whole file")
    args = ap.parse_args()

    since = parse_since(args.since)
    now = time.time()

    total, skipped, filtered = 0, 0, 0
    rows = []
    for line in open(args.path, "r", encoding="utf-8"):
        total += 1
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            skipped += 1
            continue
        ts = parse_ts(rec.get("ts"))
        if since is not None and (ts is None or ts < since):
            filtered += 1
            continue
        rows.append(rec)

    if not rows:
        print(f"judge-failure-evidence report: {total} lines read "
              f"({skipped} malformed, {filtered} before --since); no failures in window.")
        return 0

    # Synthetic-data check: test harness rows have zeroed latencies and
    # placeholder providers (p1/p2/local) with empty/'boom' excerpts.
    looks_synthetic = all(
        (r.get("latency_ms") or 0) == 0
        and str(r.get("provider") or "") in ("p1", "p2", "local", "None", "")
        for r in rows
    )

    per = {}
    for r in rows:
        name = r.get("provider") or "unknown"
        st = per.setdefault(name, {"n": 0, "by_class": Counter(),
                                   "lats": [], "last": None, "rows": []})
        st["n"] += 1
        st["by_class"][str(r.get("error_class"))] += 1
        lat = r.get("latency_ms")
        if isinstance(lat, (int, float)):
            st["lats"].append(float(lat))
        ts = parse_ts(r.get("ts"))
        if ts is not None and (st["last"] is None or ts > st["last"]):
            st["last"] = ts
        st["rows"].append(r)

    # trailing consecutive provider-class failure run, in log order
    for name, st in per.items():
        run = 0
        for r in reversed(st["rows"]):
            if str(r.get("error_class")) in PROVIDER_CLASS:
                run += 1
            else:
                break
        st["consec"] = run

    window_start = min(parse_ts(r.get("ts")) or now for r in rows)
    print("judge-failure-evidence report")
    print(f"  log:    {args.path}")
    print(f"  window: {datetime.fromtimestamp(window_start, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}"
          f" -> {datetime.fromtimestamp(now, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}"
          + (f" (--since {args.since})" if args.since else ""))
    print(f"  rows:   {len(rows)} failures of {total} lines "
          f"({skipped} malformed skipped, {filtered} outside window)")
    if looks_synthetic:
        print("  NOTE: all rows have 0.0ms latency and placeholder providers "
              "(p1/p2/local) -- log appears to hold synthetic test data only; "
              "real production distribution is still unknown.")
    print()

    grand = sum(st["n"] for st in per.values())
    for name in sorted(per, key=lambda n: per[n]["n"], reverse=True):
        st = per[name]
        lats = sorted(st["lats"])
        p50 = percentile(lats, 0.50)
        p95 = percentile(lats, 0.95)
        classes = ", ".join(f"{c}={n}" for c, n in st["by_class"].most_common())
        share = 100.0 * st["n"] / grand if grand else 0.0
        print(f"provider: {name}  ({st['n']} failures, {share:.1f}% of window)")
        print(f"  by_class:      {classes}")
        print(f"  latency_ms:    n={len(lats)}"
              f" p50={p50:.1f}" if p50 is not None else "n=0",
              f"p95={p95:.1f}" if p95 is not None else "")
        print(f"  last_failure:  {fmt_age(now - st['last']) if st['last'] else 'n/a'} ago")
        print(f"  consec_fails:  {st['consec']} (breaker trips at {ALLOWED_FAILS})")
        print(f"  recommend:     {recommend(name, {**st, 'fails': st['n'], 'p95': p95})}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
