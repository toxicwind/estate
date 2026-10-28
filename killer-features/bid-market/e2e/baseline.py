"""Naive round-robin baseline: REAL worker processes, REAL execution.

Dispatcher assigns task i -> POOL[i % len(POOL)] BLINDLY (no capability
check, no speed awareness — that naivety is the point). Workers are real
OS processes doing real work via executor.py. Tasks assigned to a bidder
lacking the capability fail for real (capability gate in executor).

Event-driven (no poll loops): per-worker wake FIFOs + a results FIFO;
the dispatcher blocks on the results fifo and wakes exactly when a
worker reports. select() with a fail-fast ceiling bounds the whole run.

Builds ledger.json:
  {task_id: {bidder, posted_ts, assigned_ts, completed_ts, status,
             out_dir, exec_s, delay_s, error}}
status: ok | failed | timeout | unassigned
"""

import json
import os
import select
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import profiles
import tasks as task_defs


def _link_fixtures(src_in, dst_in):
    for root, _, files in os.walk(src_in):
        for fn in files:
            s = os.path.join(root, fn)
            rel = os.path.relpath(s, src_in)
            d = os.path.join(dst_in, os.path.dirname(rel))
            os.makedirs(d, exist_ok=True)
            try:
                os.link(s, os.path.join(d, fn))
            except FileExistsError:
                pass


def run_baseline(run_dir, seed=1, ceiling_s=600, pool="e2e"):
    if pool == "real":
        import real_pool
        pool_names = [w for w, _ in real_pool.POOL]
    else:
        pool_names = profiles.POOL
    os.makedirs(run_dir, exist_ok=True)
    batch_in = os.path.join(run_dir, "in")
    os.makedirs(batch_in, exist_ok=True)
    for t in task_defs.TASKS:
        task_defs.materialize(t, batch_in)

    fifo_dir = os.path.join(run_dir, "fifo")
    os.makedirs(fifo_dir, exist_ok=True)
    # dispatcher holds O_RDWR on every fifo: open never blocks for anyone,
    # reads block until a writer wakes them (event-driven, zero wakeups idle)
    wfds = {}
    for name in pool_names + ["results"]:
        p = os.path.join(fifo_dir, name)
        try:
            os.mkfifo(p)
        except FileExistsError:
            pass
        wfds[name] = os.open(p, os.O_RDWR)

    here = os.path.dirname(os.path.abspath(__file__))
    procs = {}
    for name in pool_names:
        p = subprocess.Popen(
            [sys.executable, os.path.join(here, "worker.py"),
             "--name", name, "--run-dir", run_dir, "--seed", str(seed),
             "--pool", pool],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        procs[name] = p
    time.sleep(0.5)  # one-time worker boot; not a poll loop

    # blind round-robin dispatch: file first, THEN the wake byte
    for i, t in enumerate(task_defs.TASKS):
        worker = pool_names[i % len(pool_names)]
        workdir = os.path.join(run_dir, "work", t["id"])
        _link_fixtures(os.path.join(batch_in, t["id"]),
                       os.path.join(workdir, "in"))
        assignment = {"task_id": t["id"], "workdir": workdir,
                      "posted_ts": time.time()}
        inbox = os.path.join(run_dir, "inbox", worker)
        os.makedirs(inbox, exist_ok=True)
        tmp = os.path.join(inbox, "pending-%s.json.tmp" % t["id"])
        with open(tmp, "w") as f:
            json.dump(assignment, f)
        os.replace(tmp, os.path.join(inbox, "pending-%s.json" % t["id"]))
        os.write(wfds[worker], b"\x00")  # wake exactly this worker

    # event-driven wait: block on results fifo until all 16 report,
    # or the fail-fast ceiling hits (select timeout = ceiling, not a poll)
    want = {t["id"] for t in task_defs.TASKS}
    seen = set()
    res_f = os.fdopen(os.dup(wfds["results"]), "r", buffering=1)
    deadline = time.time() + ceiling_s
    while seen < want:
        remaining = deadline - time.time()
        if remaining <= 0:
            break
        r, _, _ = select.select([res_f], [], [], remaining)
        if not r:
            break  # ceiling hit
        line = res_f.readline()
        if not line:
            break
        seen.add(line.strip())

    open(os.path.join(run_dir, "STOP"), "w").write("stop")
    for name in pool_names:  # wake workers so they observe STOP
        try:
            os.write(wfds[name], b"\x00")
        except OSError:
            pass
    for p in procs.values():
        try:
            p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            p.kill()
    for fd in wfds.values():
        os.close(fd)

    # ledger
    results_dir = os.path.join(run_dir, "results")
    ledger = {}
    for i, t in enumerate(task_defs.TASKS):
        rp = os.path.join(results_dir, t["id"] + ".json")
        out_dir = os.path.join(run_dir, "work", t["id"], "out")
        if not os.path.isfile(rp):
            ledger[t["id"]] = {
                "bidder": pool_names[i % len(pool_names)],
                "posted_ts": None, "assigned_ts": None, "completed_ts": None,
                "status": "unassigned", "out_dir": out_dir}
            continue
        with open(rp) as f:
            r = json.load(f)
        m = r["manifest"]
        ledger[t["id"]] = {
            "bidder": r["worker"], "posted_ts": r["posted_ts"],
            "assigned_ts": r["assigned_ts"], "completed_ts": r["completed_ts"],
            "status": m["status"], "out_dir": out_dir,
            "exec_s": m.get("exec_s"), "delay_s": m.get("delay_s"),
            "error": m.get("error")}
    with open(os.path.join(run_dir, "ledger.json"), "w") as f:
        json.dump(ledger, f, indent=1)
    return ledger


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--pool", choices=["e2e", "real"], default="e2e")
    args = ap.parse_args()
    ledger = run_baseline(args.run_dir, args.seed, pool=args.pool)
    ok = sum(1 for v in ledger.values() if v["status"] == "ok")
    print("baseline done: %d/%d ok" % (ok, len(ledger)))
