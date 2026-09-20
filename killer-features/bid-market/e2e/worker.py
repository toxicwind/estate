"""Baseline worker: a REAL OS process that executes tasks for round-robin.

Usage: python3 worker.py --name <profile> --run-dir <dir> --seed <int>

Event-driven IPC (no polling, per doctrine):
  fifo/<name>        dispatcher writes 1 byte per assignment / STOP wake
  inbox/<name>/pending-<taskid>.json   assignment payload (atomic os.replace)
  claimed/<taskid>.json                atomic rename on claim
  results/<taskid>.json                result manifest (atomic os.replace)
  fifo/results                         worker writes "<taskid>\\n" on completion
  STOP                                 dispatcher creates -> worker drains & exits

Each task runs for REAL via executor.execute() with this worker's profile
(caps/delay/fail_rate from profiles.py). Failures are seeded deterministically
from (seed, task_id, profile) so reruns are comparable.
"""

import argparse
import json
import os
import random
import select
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import executor
import profiles
import tasks as task_defs


def resolve_profile(pool, name):
    if pool == "real":
        import real_pool
        return real_pool.worker_params_by_name(name)
    return profiles.PROFILES[name]


def drain_claims(inbox_dir, claimed_dir):
    """Atomically claim all pending tasks. Returns [(task_id, assignment)]."""
    claimed = []
    try:
        names = sorted(os.listdir(inbox_dir))
    except FileNotFoundError:
        return claimed
    for n in names:
        if not n.startswith("pending-") or not n.endswith(".json"):
            continue
        src = os.path.join(inbox_dir, n)
        task_id = n[len("pending-"):-len(".json")]
        dst = os.path.join(claimed_dir, task_id + ".json")
        try:
            os.rename(src, dst)  # atomic claim
        except FileNotFoundError:
            continue
        with open(dst) as f:
            claimed.append((task_id, json.load(f)))
    return claimed


def has_pending(inbox_dir):
    """Peek: any unclaimed assignment files? (no claim, no side effects)"""
    try:
        return any(n.startswith("pending-") and n.endswith(".json")
                   for n in os.listdir(inbox_dir))
    except FileNotFoundError:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--pool", choices=["e2e", "real"], default="e2e")
    args = ap.parse_args()

    name = args.name
    run_dir = args.run_dir
    prof = resolve_profile(args.pool, name)
    inbox_dir = os.path.join(run_dir, "inbox", name)
    claimed_dir = os.path.join(run_dir, "claimed")
    results_dir = os.path.join(run_dir, "results")
    os.makedirs(inbox_dir, exist_ok=True)
    os.makedirs(claimed_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    task_by_id = {t["id"]: t for t in task_defs.TASKS}
    stop_path = os.path.join(run_dir, "STOP")

    # dispatcher holds O_RDWR on our fifo already, so O_RDONLY never blocks
    wake_fd = os.open(os.path.join(run_dir, "fifo", name), os.O_RDONLY)
    res_fd = os.open(os.path.join(run_dir, "fifo", "results"), os.O_WRONLY)

    while True:
        # EVENT-DRIVEN wait: block until dispatcher signals work or STOP.
        # os.read on a fifo with no writers... dispatcher holds O_RDWR so
        # the read end stays valid; read blocks until a byte arrives.
        try:
            os.read(wake_fd, 1)
        except OSError:
            break
        for task_id, assignment in drain_claims(inbox_dir, claimed_dir):
            task = task_by_id[task_id]
            assigned_ts = time.time()
            workdir = os.path.join(run_dir, "work", task_id)
            rng = random.Random(hash((args.seed, task_id, name)) & 0xFFFFFFFF)
            manifest = executor.execute(task, workdir, name, prof, rng)
            completed_ts = time.time()
            result = {"task_id": task_id, "worker": name,
                      "posted_ts": assignment["posted_ts"],
                      "assigned_ts": assigned_ts, "completed_ts": completed_ts,
                      "manifest": manifest}
            tmp = os.path.join(results_dir, task_id + ".json.tmp")
            with open(tmp, "w") as f:
                json.dump(result, f)
            os.replace(tmp, os.path.join(results_dir, task_id + ".json"))
            os.write(res_fd, (task_id + "\n").encode())  # wake dispatcher
        if os.path.exists(stop_path):
            # Airtight exit: an assignment always leaves a pending file or an
            # unread wake byte (dispatcher writes file BEFORE the byte), so
            # exit only when neither exists. select(0) is a check, not a poll.
            if (not has_pending(inbox_dir)
                    and not select.select([wake_fd], [], [], 0)[0]):
                break


if __name__ == "__main__":
    main()
