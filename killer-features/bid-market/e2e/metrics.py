"""Metrics over an auction/baseline ledger + independent verification.

ledger: {task_id: {bidder, posted_ts, assigned_ts, completed_ts,
                   status, out_dir, ...}}
status in {ok, failed, timeout, unassigned}.

Metrics:
  allocation_quality   frac of assigned tasks given to oracle_best(task)
  assign_p50/p95       assigned_ts - posted_ts (assignment latency)
  complete_p50/p95     completed_ts - posted_ts for checker-passing tasks
  completion_rate      checker-passing / total
  false_completion_rate  among tasks marked ok, frac failing the checker
                         (THE e2e-real integrity metric)
  makespan_s           max completed_ts - min posted_ts
Verification is INDEPENDENT: checkers.py recomputes ground truth from
fixtures; never trusts the runner's status.
"""

import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import checkers
import profiles
import tasks as task_defs


def _pct(xs, q):
    if not xs:
        return None
    s = sorted(xs)
    i = min(int(q / 100 * len(s)), len(s) - 1)
    return s[i]


def verify_run(run_dir, ledger, task_of=None):
    """Run every task's independent checker. Returns per-task results.

    task_of: fn(task_id_in_ledger) -> task dict. Market ledgers use
    batch-prefixed ids ("e2e1-A1"); pass a stripper for those runs.
    """
    task_by_id = {t["id"]: t for t in task_defs.TASKS}
    if task_of is None:
        task_of = lambda tid: task_by_id[tid]  # noqa: E731
    results = {}
    for tid, entry in ledger.items():
        task = task_of(tid)
        in_dir = entry.get("in_dir") or os.path.join(run_dir, "in", tid)
        out_dir = entry["out_dir"]
        if entry["status"] != "ok":
            results[tid] = {"verified": False,
                            "detail": "not completed (status=%s)" % entry["status"]}
            continue
        try:
            passed, detail = checkers.check(task, in_dir, out_dir)
        except Exception as e:  # checker crash = verification failure, loud
            passed, detail = False, "CHECKER CRASH: %r" % e
        results[tid] = {"verified": passed, "detail": detail}
    return results


def _default_is_oracle(task_of):
    def is_oracle(tid, bidder_id):
        return bidder_id == profiles.oracle_best(task_of(tid))
    return is_oracle


def compute(ledger, verification, task_of=None, is_oracle=None):
    task_by_id = {t["id"]: t for t in task_defs.TASKS}
    if task_of is None:
        task_of = lambda tid: task_by_id[tid]  # noqa: E731
    if is_oracle is None:
        is_oracle = _default_is_oracle(task_of)
    total = len(ledger)
    assigned = {tid: e for tid, e in ledger.items() if e["assigned_ts"]}
    ok_marked = [tid for tid, e in ledger.items() if e["status"] == "ok"]
    verified_ok = [tid for tid in ok_marked
                   if verification.get(tid, {}).get("verified")]
    false_completed = [tid for tid in ok_marked
                       if not verification.get(tid, {}).get("verified")]

    best_hits = sum(1 for tid, e in assigned.items()
                    if e["bidder"] and is_oracle(tid, e["bidder"]))
    assign_lat = [e["assigned_ts"] - e["posted_ts"] for e in assigned.values()
                  if e["posted_ts"] and e["assigned_ts"]]
    complete_lat = [ledger[tid]["completed_ts"] - ledger[tid]["posted_ts"]
                    for tid in verified_ok
                    if ledger[tid]["posted_ts"] and ledger[tid]["completed_ts"]]
    posted = [e["posted_ts"] for e in ledger.values() if e["posted_ts"]]
    completed = [e["completed_ts"] for e in ledger.values() if e["completed_ts"]]

    return {
        "total": total,
        "assigned": len(assigned),
        "completed_ok": len(verified_ok),
        "completion_rate": len(verified_ok) / total if total else 0,
        "false_completions": len(false_completed),
        "false_completion_rate": (len(false_completed) / len(ok_marked)
                                  if ok_marked else 0),
        "allocation_quality": (best_hits / len(assigned) if assigned else 0),
        "assign_p50": _pct(assign_lat, 50),
        "assign_p95": _pct(assign_lat, 95),
        "complete_p50": _pct(complete_lat, 50),
        "complete_p95": _pct(complete_lat, 95),
        "makespan_s": (max(completed) - min(posted)
                       if posted and completed else None),
    }


def fmt(v):
    if v is None:
        return "n/a"
    if isinstance(v, float):
        return "%.3f" % v
    return str(v)


def compare_table(name_a, m_a, name_b, m_b):
    rows = [("tasks", "total"), ("assigned", "assigned"),
            ("verified completions", "completed_ok"),
            ("completion rate", "completion_rate"),
            ("false completions", "false_completions"),
            ("false-completion rate", "false_completion_rate"),
            ("allocation quality", "allocation_quality"),
            ("assign latency p50 (s)", "assign_p50"),
            ("assign latency p95 (s)", "assign_p95"),
            ("completion latency p50 (s)", "complete_p50"),
            ("completion latency p95 (s)", "complete_p95"),
            ("makespan (s)", "makespan_s")]
    lines = ["| metric | %s | %s |" % (name_a, name_b),
             "|---|---|---|"]
    for label, key in rows:
        lines.append("| %s | %s | %s |" % (label, fmt(m_a.get(key)),
                                           fmt(m_b.get(key))))
    return "\n".join(lines)
