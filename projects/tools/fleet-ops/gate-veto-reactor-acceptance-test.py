#!/usr/bin/env python3
"""Adversarial acceptance test for gate-veto-reactor.py (plan/ack protocol).

Uses REAL veto rows (job_id + sched_utc) from the 2026-09-17 ~02:29 MDT
veto episode, plus the known false-positive traps:
  - quoted-notice rows (acfix-skip-reconcile execution reports quote the
    notice; 2026-09-18 false-positive fix)
  - overlap-skip, genuine, coalesced, in-flight rows
  - stale vetoes outside the 2h lookback
  - non-allowlisted vetoed jobs (ask-complete-watchdog mutates ledgers;
    whatsapp-fleet-digest quarantined 2026-09-19: chat-facing poster)
  - plan/ack: watermarks advance ONLY via --ack after successful dispatch;
    un-acked entries stay retryable; double-ack / unknown-ack / non-
    allowlisted-ack exit 2 fail-closed
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
    {"job_id": "whatsapp-fleet-digest", "status": "succeeded",
     "result_summary": NOTICE1, "sched_utc": 1789634440},
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


def make_wrapper(state_dir):
    wrapper = os.path.join(state_dir, "wrapper.py")
    src = open(SCRIPT).read()
    src = src.replace(
        'GOAL_DIR = os.path.expanduser(\n    "~/workspace/goals/safety-review-gate-investigation")',
        f'GOAL_DIR = {state_dir!r}')
    open(wrapper, "w").write(src)
    return wrapper


def run_plan(wrapper, rows):
    p = subprocess.run([sys.executable, wrapper], input=json.dumps(rows),
                       capture_output=True, text=True, timeout=30)
    return p


def run_ack(wrapper, record_id):
    p = subprocess.run([sys.executable, wrapper, "--ack", record_id],
                       capture_output=True, text=True, timeout=30)
    return p


def manifest_of(state_dir):
    with open(os.path.join(state_dir, "hidden_files",
                            "gate-veto-reactor-manifest.json")) as f:
        return json.load(f)


def state_of(state_dir):
    with open(os.path.join(state_dir, "hidden_files",
                            "gate-veto-reactor-state.json")) as f:
        return json.load(f)


def counts_of(p):
    line = [l for l in p.stdout.splitlines() if "classification counts" in l][0]
    return json.loads(line.split("counts: ", 1)[1])


def fresh_rows():
    rows = []
    for r in VETO_ROWS:
        r2 = dict(r)
        stale = r2.pop("keep_stale", False)
        if not stale and r2["sched_utc"] < NOW - 7200:
            r2["sched_utc"] = NOW - 600
        rows.append(r2)
    return rows + TRAP_ROWS


def main():
    state_dir = tempfile.mkdtemp(prefix="gvr-test-")
    wrapper = make_wrapper(state_dir)
    rows = fresh_rows()

    # Run 1: plan. Manifest has planned entries; watermarks NOT advanced.
    p = run_plan(wrapper, rows)
    check("plan exit 0", p.returncode == 0,
          f"rc={p.returncode} stderr={p.stderr[:200]}")
    man = manifest_of(state_dir)
    ids = sorted(m["job_id"] for m in man)
    check("vetoed allowlisted jobs planned",
          ids == ["service-restart-watchdog", "sidechat-watch-agent2",
                  "sidechat-watch-safety"],
          f"got {ids}")
    check("all entries dispatch=planned",
          all(m.get("dispatch") == "planned" for m in man))
    check("watermarks NOT advanced by plan (failed dispatch stays retryable)",
          state_of(state_dir) == {}, f"got {state_of(state_dir)}")
    check("ask-complete-watchdog NOT planned (mutating, not allowlisted)",
          "ask-complete-watchdog" not in ids)
    check("whatsapp-fleet-digest NOT planned (quarantined chat-facing)",
          "whatsapp-fleet-digest" not in ids)
    check("stale veto outside lookback ignored",
          "fleet-snapshot-5m" not in ids)
    counts = counts_of(p)
    check("quoted-notice row NOT counted as vetoed",
          counts.get("vetoed", 0) == 6, f"counts={counts}")
    check("vetoed-not-allowlisted counted (ask-complete + whatsapp)",
          counts.get("vetoed-not-allowlisted", 0) == 2, f"counts={counts}")
    check("quoted-notice classified executed",
          counts.get("executed", 0) >= 2, f"counts={counts}")
    check("overlap-skip classified", counts.get("overlap-skip", 0) == 1)
    check("in-flight classified", counts.get("in-flight", 0) == 1)
    check("cancelled classified", counts.get("cancelled", 0) == 1)

    # Ack one entry: watermark advances, entry leaves the manifest.
    rec = f"sidechat-watch-safety@{man[0]['vetoed_sched_utc']}" \
        if man[0]["job_id"] == "sidechat-watch-safety" else None
    entry = next(m for m in man if m["job_id"] == "sidechat-watch-safety")
    rec = f"{entry['job_id']}@{entry['vetoed_sched_utc']}"
    pa = run_ack(wrapper, rec)
    check("ack exit 0", pa.returncode == 0, f"stderr={pa.stderr[:200]}")
    st = state_of(state_dir)
    check("watermark advanced by ack",
          st.get("sidechat-watch-safety", {}).get("last_veto_redriven_utc")
          == entry["vetoed_sched_utc"], f"got {st}")
    man_after = manifest_of(state_dir)
    check("acked entry leaves manifest",
          sorted(m["job_id"] for m in man_after)
          == ["service-restart-watchdog", "sidechat-watch-agent2"])

    # Fail-closed acks.
    check("double-ack exits 2", run_ack(wrapper, rec).returncode == 2)
    check("ack unknown entry exits 2",
          run_ack(wrapper, "sidechat-watch-safety@1234567890").returncode == 2)
    check("ack non-allowlisted job exits 2",
          run_ack(wrapper, "ask-complete-watchdog@1789634436").returncode == 2)
    check("ack malformed record exits 2",
          run_ack(wrapper, "not-a-record").returncode == 2)
    check("failed acks leave state untouched",
          state_of(state_dir) == st)

    # Run 2: replan WITHOUT acking the remaining two (simulates failed
    # dispatch) -> they stay planned and retryable, not suppressed.
    p2 = run_plan(wrapper, rows)
    man2 = manifest_of(state_dir)
    check("un-acked entries stay planned on replan (retryable)",
          sorted(m["job_id"] for m in man2)
          == ["service-restart-watchdog", "sidechat-watch-agent2"]
          and all(m.get("dispatch") == "planned" for m in man2),
          f"got {man2}")
    check("no duplicate planned entries", len(man2) == 2)

    # Ack the remaining two, then replan -> clean, already-redriven counted.
    for m in man2:
        r = run_ack(wrapper, f"{m['job_id']}@{m['vetoed_sched_utc']}")
        check(f"ack {m['job_id']} ok", r.returncode == 0)
    p3 = run_plan(wrapper, rows)
    check("clean manifest after all acked", manifest_of(state_dir) == [])
    c3 = counts_of(p3)
    check("already-redriven counted", c3.get("vetoed-already-redriven", 0) == 3,
          f"counts={c3}")

    # Malformed input -> exit 2.
    state_dir4 = tempfile.mkdtemp(prefix="gvr-test4-")
    w4 = make_wrapper(state_dir4)
    p4 = subprocess.run([sys.executable, w4], input="{not json",
                        capture_output=True, text=True, timeout=30)
    check("malformed input -> exit 2", p4.returncode == 2)

    # Newer veto for an acked job replans (watermark is per-veto, newest wins).
    rows_new = fresh_rows()
    for r in rows_new:
        if r["job_id"] == "sidechat-watch-agent2" and r["status"] == "succeeded" \
                and "safety review" in (r.get("result_summary") or "") \
                and r["result_summary"] in (
                    "Skipped this scheduled run because its task definition did not pass the scheduled-task safety review.",
                    "Skipped this scheduled run because its task definition or goal guide did not pass the scheduled-task safety review."):
            r["sched_utc"] = NOW - 60
    p5 = run_plan(wrapper, rows_new)
    man5 = manifest_of(state_dir)
    check("newer veto replans after ack",
          [m["job_id"] for m in man5] == ["sidechat-watch-agent2"],
          f"got {man5}")

    print()
    if FAILURES:
        print("FAILURES:", FAILURES)
        return 1
    print("ALL ACCEPTANCE TESTS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
