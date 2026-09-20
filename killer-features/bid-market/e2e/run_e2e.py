"""Top-level e2e driver. Runs ON YOTE (all heavy compute stays on yote).

  python3 run_e2e.py selftest --run-dir <dir>
      Materialize fixtures, execute every task via executor with a
      competent profile, run INDEPENDENT checkers (must all pass), then
      corrupt each output and confirm checkers catch it (must all fail).
      Proves the batch + checkers are real before any market run.

  python3 run_e2e.py baseline --run-dir <dir> [--seed N]
      Naive blind round-robin over 5 real worker processes -> ledger.json
      + metrics printed. This is the baseline the market must beat.

  python3 run_e2e.py market --run-dir <dir> --batch <id> [--seed N]
      Launch real bidder processes, post the batch through the REAL
      squawk marketplace, collect the auction ledger, verify every
      result INDEPENDENTLY. Fails loud until auctioneer+bidder land.

  python3 run_e2e.py verify --run-dir <dir>
      Independent verification of an existing run's ledger -> report.

  python3 run_e2e.py report --market <ledger> --baseline <ledger> --out <md>
      Auction vs round-robin comparison table + confidence assessment.
"""

import argparse
import json
import os
import random
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import auctioneer_driver
import baseline as baseline_mod
import bidder_launcher
import checkers
import executor
import metrics
import profiles
import real_pool
import tasks as task_defs


def _task_of_for(ledger):
    """Market ledgers use batch-prefixed ids; map back to task dicts."""
    task_by_id = {t["id"]: t for t in task_defs.TASKS}
    sample = next(iter(ledger))
    if "-" in sample and sample not in task_by_id:
        return lambda tid: task_by_id[tid.rsplit("-", 1)[-1]]  # noqa: E731
    return lambda tid: task_by_id[tid]  # noqa: E731


def _is_oracle_for(ledger, pool):
    task_of = _task_of_for(ledger)
    if pool == "real":
        return task_of, lambda tid, b: real_pool.is_oracle_win(
            task_of(tid), b)
    return task_of, None  # None -> metrics default (e2e profiles oracle)


def cmd_selftest(args):
    run_dir = args.run_dir
    if os.path.exists(run_dir):
        shutil.rmtree(run_dir)
    batch_in = os.path.join(run_dir, "in")
    prof = {"caps": {"shell", "python"}, "delay_s": 0.0, "fail_rate": 0.0}
    fails = []
    for t in task_defs.TASKS:
        in_dir = task_defs.materialize(t, batch_in)
        workdir = os.path.join(run_dir, "work", t["id"])
        os.makedirs(os.path.join(workdir, "in"), exist_ok=True)
        # hardlink fixtures into workdir (same layout bidders see)
        for root, _, files in os.walk(in_dir):
            for fn in files:
                s = os.path.join(root, fn)
                rel = os.path.relpath(s, in_dir)
                d = os.path.join(workdir, "in", os.path.dirname(rel))
                os.makedirs(d, exist_ok=True)
                os.link(s, os.path.join(d, fn))
        rng = random.Random(999)
        m = executor.execute(t, workdir, "selftest", prof, rng)
        out_dir = os.path.join(workdir, "out")
        if m["status"] != "ok":
            fails.append((t["id"], "executor %s: %s" % (m["status"], m["error"])))
            continue
        try:
            passed, detail = checkers.check(t, in_dir, out_dir)
        except Exception as e:
            passed, detail = False, "CHECKER CRASH: %r" % e
        print("  [%s] executor=%s checker=%s (%s)" %
              (t["id"], m["status"], "PASS" if passed else "FAIL", detail))
        if not passed:
            fails.append((t["id"], "checker rejected good output: " + detail))
            continue
        # negative control: corrupt the outputs -> checker MUST fail
        for fn in task_defs.expected_outputs(t):
            p = os.path.join(out_dir, fn)
            if os.path.isfile(p):
                with open(p, "ab") as f:
                    f.write(b"\nCORRUPT\n")
        try:
            passed2, detail2 = checkers.check(t, in_dir, out_dir)
        except Exception as e:
            passed2, detail2 = False, "checker crashed on corrupt: %r" % e
        if passed2:
            fails.append((t["id"], "checker ACCEPTED corrupted output!"))
        else:
            print("  [%s] negative control OK (rejected: %s)" %
                  (t["id"], detail2[:60]))
    if fails:
        print("SELFTEST FAILED:")
        for tid, why in fails:
            print("  %s: %s" % (tid, why))
        sys.exit(1)
    print("SELFTEST GREEN: 16/16 tasks execute for real, checkers verify, "
          "corruption caught.")


def cmd_baseline(args):
    t0 = time.time()
    ledger = baseline_mod.run_baseline(args.run_dir, args.seed, pool=args.pool)
    task_of, is_oracle = _is_oracle_for(ledger, args.pool)
    verification = metrics.verify_run(args.run_dir, ledger, task_of=task_of)
    m = metrics.compute(ledger, verification, task_of=task_of,
                        is_oracle=is_oracle)
    with open(os.path.join(args.run_dir, "metrics.json"), "w") as f:
        json.dump({"metrics": m, "verification": verification,
                   "pool": args.pool}, f, indent=1)
    print("baseline wall %.1fs (pool=%s)" % (time.time() - t0, args.pool))
    print(json.dumps(m, indent=1))
    bad = [tid for tid, v in verification.items() if not v["verified"]
           and ledger[tid]["status"] == "ok"]
    if bad:
        print("FALSE COMPLETIONS (claimed ok, checker failed): %s" % bad)


def cmd_market(args):
    run_dir = args.run_dir
    print("launching 5 REAL bidder.py processes...")
    procs = bidder_launcher.launch(run_dir)
    try:
        print("running market auction via auctioneer_driver "
              "(PROTOCOL.md v0)...")
        ledger = auctioneer_driver.run_market(run_dir, args.batch)
    finally:
        bidder_launcher.stop(procs)
    task_of, is_oracle = _is_oracle_for(ledger, "real")
    verification = metrics.verify_run(run_dir, ledger, task_of=task_of)
    m = metrics.compute(ledger, verification, task_of=task_of,
                        is_oracle=is_oracle)
    with open(os.path.join(run_dir, "metrics.json"), "w") as f:
        json.dump({"metrics": m, "verification": verification,
                   "pool": "real", "batch": args.batch}, f, indent=1)
    print(json.dumps(m, indent=1))
    bad = [tid for tid, v in verification.items() if not v["verified"]
           and ledger[tid]["status"] == "ok"]
    if bad:
        print("FALSE COMPLETIONS (claimed ok, checker failed): %s" % bad)


def cmd_verify(args):
    with open(os.path.join(args.run_dir, "ledger.json")) as f:
        ledger = json.load(f)
    task_of, is_oracle = _is_oracle_for(ledger, args.pool)
    verification = metrics.verify_run(args.run_dir, ledger, task_of=task_of)
    m = metrics.compute(ledger, verification, task_of=task_of,
                        is_oracle=is_oracle)
    print(json.dumps(m, indent=1))
    for tid, v in verification.items():
        print("  [%s] bidder=%s status=%s verified=%s (%s)" % (
            tid, ledger[tid]["bidder"], ledger[tid]["status"],
            v["verified"], v["detail"][:70]))


CONFIDENCE_TEMPLATE = """# Bid-Marketplace E2E Report

Batch: {batch} | {n} tasks, {pool} bidder profiles | {date}

## Auction vs round-robin

{compare}

## Per-task ledger (market)

| task | category | bidder | oracle-best | status | verified | assign->done (s) |
|---|---|---|---|---|---|---|
{task_rows}

## Confidence assessment

{confidence}
"""


def cmd_report(args):
    with open(args.market) as f:
        market_ledger = json.load(f)
    with open(args.baseline) as f:
        baseline_ledger = json.load(f)
    mkt_task_of, mkt_oracle = _is_oracle_for(market_ledger, args.market_pool)
    base_task_of, base_oracle = _is_oracle_for(baseline_ledger,
                                              args.baseline_pool)
    m_mkt = metrics.compute(market_ledger, metrics.verify_run(
        os.path.dirname(os.path.abspath(args.market)), market_ledger,
        task_of=mkt_task_of), task_of=mkt_task_of, is_oracle=mkt_oracle)
    m_base = metrics.compute(baseline_ledger, metrics.verify_run(
        os.path.dirname(os.path.abspath(args.baseline)), baseline_ledger,
        task_of=base_task_of), task_of=base_task_of, is_oracle=base_oracle)
    task_by_id = {t["id"]: t for t in task_defs.TASKS}
    rows = []
    for tid, e in market_ledger.items():
        t = mkt_task_of(tid)
        v = metrics.verify_run(
            os.path.dirname(os.path.abspath(args.market)), market_ledger,
            task_of=mkt_task_of)[tid]
        lat = ""
        if e["assigned_ts"] and e["completed_ts"]:
            lat = "%.2f" % (e["completed_ts"] - e["assigned_ts"])
        oracle = (real_pool.oracle_best(t) if args.market_pool == "real"
                  else profiles.oracle_best(t))
        rows.append("| %s | %s | %s | %s | %s | %s | %s |" % (
            tid, t["category"], e["bidder"], oracle, e["status"],
            v["verified"], lat))
    doc = CONFIDENCE_TEMPLATE.format(
        batch=args.batch, n=len(task_defs.TASKS), pool=len(profiles.POOL),
        date=time.strftime("%Y-%m-%d"),
        compare=metrics.compare_table("market", m_mkt,
                                      "round-robin", m_base),
        task_rows="\n".join(rows),
        confidence="(filled by t2-e2e after the market run — see notes)\n")
    with open(args.out, "w") as f:
        f.write(doc)
    print("wrote %s" % args.out)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("selftest")
    p.add_argument("--run-dir", required=True)
    p = sub.add_parser("baseline")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--pool", choices=["e2e", "real"], default="e2e")
    p = sub.add_parser("market")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--batch", required=True)
    p.add_argument("--seed", type=int, default=1)
    p = sub.add_parser("verify")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--pool", choices=["e2e", "real"], default="real")
    p = sub.add_parser("report")
    p.add_argument("--market", required=True)
    p.add_argument("--baseline", required=True)
    p.add_argument("--market-pool", choices=["e2e", "real"], default="real")
    p.add_argument("--baseline-pool", choices=["e2e", "real"], default="real")
    p.add_argument("--batch", default="batch-1")
    p.add_argument("--out", required=True)
    args = ap.parse_args()
    {"selftest": cmd_selftest, "baseline": cmd_baseline,
     "market": cmd_market, "verify": cmd_verify,
     "report": cmd_report}[args.cmd](args)


if __name__ == "__main__":
    main()
