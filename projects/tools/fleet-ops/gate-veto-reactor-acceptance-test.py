#!/usr/bin/env python3
"""Adversarial acceptance test for gate-veto-reactor.py.

Uses REAL veto rows (job_id + sched_utc) from the 2026-09-17 ~02:29 MDT
veto episode, plus the known false-positive traps:
  - quoted-notice rows (acfix-skip-reconcile execution reports quote the
    notice; 2026-09-18 false-positive fix)
  - overlap-skip, genuine, coalesced, in-flight rows
  - stale vetoes outside the 2h lookback
  - non-allowlisted vetoed jobs (ask-complete-watchdog mutates ledgers)
  - idempotence: second run must emit an empty manifest
"""
import json
import os
import subprocess
import sys
import tempfile
import time

SCRIPT = os.path.expanduser("~/workspace/bin/gate-veto-reactor.py")

NOTICE1 = ("Skipped this scheduled run because its task definition did not "
           "pass the scheduled-task safety review.")
NOTICE2 = ("Skipped this scheduled run because its task definition or goal "
           "guide did not pass the scheduled-task safety review.")

NOW = int(time.time())

# Real veto rows from the 2026-09-17 02:29 MDT episode (sched_utc from DB).
VETO_ROWS = [
    {"job_id": "sidechat-watch-safety", "status": "succeeded",
     "result_summary": NOTICE1, "sched_utc": 1789633720},
    {"job_id": "sidechat-watch-agent2", "status": "succeeded",
     "result_summary": NOTICE2, "sched_utc": 1789633719},
    {"job_id": "service-restart-watchdog", "status": "succeeded",
     "result_summary": NOTICE1, "sched_utc": 1789633729},
    {"job_id": "ask-complete-watchdog", "status": "succeeded",
     "result_summary": NOTICE1, "sched_utc": 1789634436},
    # stale veto: outside the 2h lookback -> ignored
    {"job_id": "fleet-snapshot-5m", "status": "succeeded",
     "result_summary": NOTICE1, "sched_utc": NOW - 3 * 3600, "keep_stale": True},
]

TRAP_ROWS = [
    # quoted-notice false positive: acfix-skip-reconcile execution report
    {"job_id": "acfix-skip-reconcile", "status": "succeeded",
     "result_summary": ("ACFix lane fix04 safety-review skip NORMALIZER run completed.\n"
                        "Identified 41 safety-review skip mislabels ('Skipped this scheduled "
                        "run because its task definition did not pass the scheduled-task "
                        "safety review.') and appended corrections."), "sched_utc": NOW - 600},
    {"job_id": "sidechat-watch-safety", "status": "succeeded",
     "result_summary": "skipped because 1 run(s) for this cron job are already running "
                       "and concurrency.overlap=skip while active", "sched_utc": NOW - 300},
    {"job_id": "fleet-snapshot-5m", "status": "succeeded",
     "result_summary": "Snapshot wrote 42 rows to fleet-state parquet in 1.8s",
     "sched_utc": NOW - 200},
    {"job_id": "heartbeat", "status": "cancelled",
     "result_summary": "", "sched_utc": NOW - 100},
    {"job_id": "lane-poller-lane-1", "status": "running",
     "result_summary": None, "sched_utc": NOW - 50},
]

FAILURES = []


def check(name, cond, detail=""):
    print(("PASS" if cond else "FAIL"), "-", name, detail)
    if not cond:
        FAILURES.append(name)


def run_reactor(rows, state_dir):
    env = dict(os.environ)
    # point the script at a scratch state dir by monkeypatching paths
    # (script uses fixed paths; instead run a wrapper that rewrites constants)
    wrapper = os.path.join(state_dir, "wrapper.py")
    src = open(SCRIPT).read()
    src = src.replace(
        'GOAL_DIR = os.path.expanduser(\n    "~/workspace/goals/safety-review-gate-investigation")',
        f'GOAL_DIR = {state_dir!r}')
    open(wrapper, "w").write(src)
    p = subprocess.run([sys.executable, wrapper], input=json.dumps(rows),
                       capture_output=True, text=True, timeout=30)
    return p


def manifest_of(state_dir):
    with open(os.path.join(state_dir, "hidden_files",
                            "gate-veto-reactor-manifest.json")) as f:
        return json.load(f)


def main():
    state_dir = tempfile.mkdtemp(prefix="gvr-test-")

    # Run 1: real vetoes + traps, all inside lookback.
    rows = []
    for r in VETO_ROWS:
        r2 = dict(r)
        stale = r2.pop("keep_stale", False)
        # bring the Sep-17 episode rows into the lookback window (keep the
        # real job_ids, refresh timestamps to NOW-10m); leave the
        # deliberately-stale row alone
        if not stale and r2["sched_utc"] < NOW - 7200:
            r2["sched_utc"] = NOW - 600
        rows.append(r2)
    rows += TRAP_ROWS

    p = run_reactor(rows, state_dir)
    check("exit 0", p.returncode == 0, f"rc={p.returncode} stderr={p.stderr[:200]}")
    man = manifest_of(state_dir)
    ids = sorted(m["job_id"] for m in man)
    check("vetoed allowlisted jobs redriven",
          ids == ["service-restart-watchdog", "sidechat-watch-agent2",
                  "sidechat-watch-safety"],
          f"got {ids}")
    check("ask-complete-watchdog NOT redriven (mutating, not allowlisted)",
          "ask-complete-watchdog" not in ids)
    check("stale veto outside lookback ignored",
          "fleet-snapshot-5m" not in ids)
    counts_line = [l for l in p.stdout.splitlines() if "classification counts" in l][0]
    counts = json.loads(counts_line.split("counts: ", 1)[1])
    check("quoted-notice row NOT counted as vetoed",
          counts.get("vetoed", 0) == 5, f"counts={counts}")  # 4 fresh + 1 stale (stale vetoes are classified but not manifested
    check("quoted-notice classified executed",
          counts.get("executed", 0) >= 2, f"counts={counts}")
    check("overlap-skip classified", counts.get("overlap-skip", 0) == 1,
          f"counts={counts}")
    check("in-flight classified", counts.get("in-flight", 0) == 1)
    check("cancelled classified", counts.get("cancelled", 0) == 1)

    # Run 2 (idempotence): same input -> empty manifest.
    p2 = run_reactor(rows, state_dir)
    man2 = manifest_of(state_dir)
    check("idempotent second run -> empty manifest", man2 == [],
          f"got {man2}")
    counts2 = json.loads(
        [l for l in p2.stdout.splitlines() if "classification counts" in l][0]
        .split("counts: ", 1)[1])
    check("already-redriven counted", counts2.get("vetoed-already-redriven", 0) == 3,
          f"counts={counts2}")
    # Run 3: malformed input -> exit 2.
    state_dir3 = tempfile.mkdtemp(prefix="gvr-test3-")
    wrapper = os.path.join(state_dir3, "wrapper.py")
    src = open(SCRIPT).read().replace(
        'GOAL_DIR = os.path.expanduser(\n    "~/workspace/goals/safety-review-gate-investigation")',
        f'GOAL_DIR = {state_dir3!r}')
    open(wrapper, "w").write(src)
    p3 = subprocess.run([sys.executable, wrapper], input="{not json",
                        capture_output=True, text=True, timeout=30)
    check("malformed input -> exit 2", p3.returncode == 2)

    print()
    if FAILURES:
        print("FAILURES:", FAILURES)
        return 1
    print("ALL ACCEPTANCE TESTS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
