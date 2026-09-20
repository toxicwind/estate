#!/usr/bin/env python3
"""Bounded concurrency check for fleet_log.append (spawn-safe: __main__ guard)."""
import multiprocessing as mp
import sys

sys.path.insert(0, "/home/toxic/.shingle/chat")
import fleet_log

ROOT = "/tmp/fltest2"
CHANNEL = "load"
WORKERS = 4
PER_WORKER = 25


def worker(w):
    base = w * PER_WORKER
    for i in range(PER_WORKER):
        seq = base + i + 1
        fleet_log.append(
            ROOT, CHANNEL, seq=seq,
            agent="w%d" % w, type="chat",
            body="x" * (100 + seq), fsync=False,
        )


def main():
    import shutil
    from pathlib import Path
    shutil.rmtree(ROOT, ignore_errors=True)
    Path(ROOT, CHANNEL).mkdir(parents=True)
    with mp.Pool(WORKERS) as p:
        p.map(worker, range(WORKERS))
    fleet_log.fsync_log(ROOT, CHANNEL)
    recs = list(fleet_log.replay(ROOT, CHANNEL))
    total = WORKERS * PER_WORKER
    seqs = sorted(r["seq"] for r in recs)
    assert len(recs) == total, "lines=%d expected=%d" % (len(recs), total)
    assert seqs == list(range(1, total + 1)), "seq gap/dup"
    assert all(r["body"] == "x" * (100 + r["seq"]) for r in recs), "body corruption"
    print("CONCURRENCY OK: %d records, %d writers, zero interleave, zero loss"
          % (total, WORKERS))


if __name__ == "__main__":
    main()
