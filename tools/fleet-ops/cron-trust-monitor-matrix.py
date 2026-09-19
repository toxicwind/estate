#!/usr/bin/env python3
"""
cron-trust-monitor-matrix: classification test matrix for cron-trust-monitor.

Covers the honest-status taxonomy (genuine / vetoed / overlap-skip / no-op /
coalesced / failed / timeout / quota-deferred / ambiguous) with special
attention to HONEST-RECEIPT footers in BOTH production syntax (unquoted
fields:  HONEST-RECEIPT job=x verdict=genuine ...)
and fixture syntax (quoted fields: HONEST-RECEIPT job="x" verdict="genuine" ...).

Key invariants under test:
  - quoted, unquoted, and mixed footers all parse;
  - a failed receipt is NEVER overridden by positive-evidence heuristics;
  - a vetoed run is never laundered into genuine.

Usage: bin/cron-trust-monitor-matrix.py   (exit 0 iff all cases pass)
"""
import importlib.util
import os
import sys

MONITOR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "cron-trust-monitor")


def load_monitor():
    loader = importlib.machinery.SourceFileLoader("cron_trust_monitor", MONITOR)
    spec = importlib.util.spec_from_loader("cron_trust_monitor", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


# (name, run dict, expected honest status; None = excluded from trust math)
CASES = [
    # --- HONEST-RECEIPT: exact production syntax (unquoted fields) ---
    ("prod genuine unquoted",
     {"status": "succeeded",
      "result_summary": "HONEST-RECEIPT job=sidechat-watch-agent1 verdict=genuine duration_s=12 work=watched evidence=/tmp/l",
      "error_text": ""}, "genuine"),
    ("prod no-op unquoted",
     {"status": "succeeded",
      "result_summary": "HONEST-RECEIPT job=heartbeat verdict=no-op duration_s=3 work=idle evidence=none",
      "error_text": ""}, "no-op"),
    ("prod failed unquoted",
     {"status": "succeeded",
      "result_summary": "HONEST-RECEIPT job=cell-backup verdict=failed duration_s=9 work=timeout evidence=none",
      "error_text": ""}, "failed"),
    # --- HONEST-RECEIPT: quoted fixture syntax ---
    ("fixture genuine quoted",
     {"status": "succeeded",
      "result_summary": 'HONEST-RECEIPT job="x" verdict="genuine" duration_s=42 work="checked X" evidence="/tmp/e"',
      "error_text": ""}, "genuine"),
    ("fixture no-op quoted",
     {"status": "succeeded",
      "result_summary": 'HONEST-RECEIPT job="x" verdict="no-op" duration_s=3 work="idle" evidence="none"',
      "error_text": ""}, "no-op"),
    ("fixture failed quoted",
     {"status": "succeeded",
      "result_summary": 'HONEST-RECEIPT job="x" verdict="failed" duration_s=9 work="db timeout" evidence="none"',
      "error_text": ""}, "failed"),
    # --- mixed quoting ---
    ("mixed quoted work unquoted rest",
     {"status": "succeeded",
      "result_summary": 'HONEST-RECEIPT job=ask-complete-watchdog verdict=genuine duration_s=61 work="3 sources ok, 0 new" evidence=/tmp/runs',
      "error_text": ""}, "genuine"),
    ("quoted job with spaces",
     {"status": "succeeded",
      "result_summary": 'HONEST-RECEIPT job="my job" verdict="failed" duration_s=5 work="db timeout" evidence="none"',
      "error_text": ""}, "failed"),
    # --- failed receipt must NOT be overridden by positive-evidence prose ---
    ("failed receipt + work-evidence prose stays failed",
     {"status": "succeeded",
      "result_summary": ('checks performed: 42 rows scanned, 0 errors, completed with 3 audits in 61s. '
                         'HONEST-RECEIPT job=x verdict=failed duration_s=61 work="db timeout" evidence=none'),
      "error_text": ""}, "failed"),
    ("failed receipt quoted + work-evidence prose stays failed",
     {"status": "succeeded",
      "result_summary": ('checks performed: 42 rows scanned, 0 errors, completed with 3 audits in 61s. '
                         'HONEST-RECEIPT job="x" verdict="failed" duration_s="61" work="db timeout" evidence="none"'),
      "error_text": ""}, "failed"),
    # --- invalid / absent receipts ---
    ("bogus verdict is not a receipt",
     {"status": "succeeded",
      "result_summary": "HONEST-RECEIPT job=x verdict=bogus work=w",
      "error_text": ""}, "ambiguous"),
    ("truncated footer is not a receipt",
     {"status": "succeeded",
      "result_summary": "HONEST-RECEIPT job=x verdict=genuine",
      "error_text": ""}, "ambiguous"),
    # --- badge-honest terminals ---
    ("failed status",
     {"status": "failed", "result_summary": "",
      "error_text": "db statement timeout"}, "failed"),
    ("timeout status",
     {"status": "timeout", "result_summary": "", "error_text": ""}, "timeout"),
    ("cancelled without detail",
     {"status": "cancelled", "result_summary": "", "error_text": ""}, "ambiguous"),
    ("non-terminal running excluded",
     {"status": "running", "result_summary": "still going", "error_text": ""}, None),
    # --- coalesced precedence ---
    ("coalesced via error text",
     {"status": "succeeded",
      "result_summary": "HONEST-RECEIPT job=x verdict=genuine duration_s=1 work=ok evidence=none",
      "error_text": "scheduled_occurrence_coalesced"}, "coalesced"),
    # --- veto laundering resistance ---
    ("vetoed short canonical",
     {"status": "succeeded",
      "result_summary": "did not pass the scheduled-task safety review",
      "error_text": ""}, "vetoed"),
    ("veto mentioned in long detailed report stays genuine",
     {"status": "succeeded",
      "result_summary": ("work performed: scanned 128 runs across 14 jobs in 2026-09-19 window; "
                         "0 safety-review vetoes found; 3 overlap-skips; trust rate 94%. "
                         "Completed with 0 errors in 44s."),
      "error_text": ""}, "genuine"),
    # --- skip / no-op / quota ---
    ("overlap-skip",
     {"status": "succeeded",
      "result_summary": "Skipped: another run was active for this job (concurrency.overlap=skip)",
      "error_text": ""}, "overlap-skip"),
    ("heartbeat no-op",
     {"status": "succeeded",
      "result_summary": "skipped heartbeat because nothing changed since last tick",
      "error_text": ""}, "no-op"),
    ("quota-deferred",
     {"status": "succeeded",
      "result_summary": "quota guard deferred this run to next window",
      "error_text": ""}, "quota-deferred"),
    # --- null / thin summaries ---
    ("null summary succeeded",
     {"status": "succeeded", "result_summary": None, "error_text": ""}, "ambiguous"),
    ("empty summary succeeded",
     {"status": "succeeded", "result_summary": "   ", "error_text": ""}, "ambiguous"),
    ("thin summary without evidence",
     {"status": "succeeded", "result_summary": "ok", "error_text": ""}, "ambiguous"),
    # --- positive-evidence rule ---
    ("counts summary is genuine",
     {"status": "succeeded",
      "result_summary": "checked 128 runs across 14 jobs; 3 overlap-skips; trust 94%; 0 errors in 44s",
      "error_text": ""}, "genuine"),
    ("verbatim WATCH-OK line is genuine",
     {"status": "succeeded",
      "result_summary": "WATCH-OK madeon | wm=1723 | new=0 unhandled=0 | clean",
      "error_text": ""}, "genuine"),
    ("wrapped WATCH-OK line is genuine",
     {"status": "succeeded",
      "result_summary": ("Side-chat watchdog run agent2 at Sat 2026-09-19 04:25:00 MDT completed: "
                         "WATCH-OK agent2 | wm=16036 | new=0 unhandled=0 | clean"),
      "error_text": ""}, "genuine"),
    # --- WATCH-FAIL lines: honest execution, failed check -> failed ---
    ("WATCH-FAIL read timeout is failed not genuine",
     {"status": "succeeded",
      "result_summary": ("WATCH-FAIL madeon | read | muse.db failed: muse.db exceeded its 5000ms "
                         "total time limit | wm=1723 unchanged"),
      "error_text": ""}, "failed"),
    ("WATCH-FAIL bootstrap sentinel is failed",
     {"status": "succeeded",
      "result_summary": ("WATCH-FAIL agent1 | rows | bootstrap_failed: aid 8a756bd0 has no usable "
                         "transcript tip | wm=-1 unchanged"),
      "error_text": ""}, "failed"),
    ("WATCH-FAIL embedded in prose with counts stays failed",
     {"status": "succeeded",
      "result_summary": ("checks performed: 61s elapsed, 3 attempts, 0 rows. "
                         "WATCH-FAIL whatsapp | query | db pool timed out | wm=2522 unchanged"),
      "error_text": ""}, "failed"),
]


def main():
    mod = load_monitor()
    classify = mod.classify_run
    failures = []
    for name, run, want in CASES:
        got, reason = classify(run)
        ok = (got == want)
        print("%s %-55s want=%-12s got=%-12s (%s)"
              % ("PASS" if ok else "FAIL", name, want, got, reason[:60]))
        if not ok:
            failures.append(name)
    print("\n%d/%d cases pass" % (len(CASES) - len(failures), len(CASES)))
    if failures:
        print("FAILURES:", failures)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
