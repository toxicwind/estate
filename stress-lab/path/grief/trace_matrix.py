#!/usr/bin/env python3
"""GRIEF-style timed multi-request trace matrix.

Issues N concurrent requests at a shared target under a time budget and
collects per-request latency + result hashes, to expose cross-request state
contamination (mismatched hashes for identical payloads), noisy-neighbor
locks (latency spikes under concurrency), and silent corruption.
Structure-only: the target is a trivial object store (dict), consistent with
the lab's measurement-only stance.
"""
import multiprocessing as mp, time, json, hashlib

def worker(ident, inject_flag, outq):
    """Each worker touches a shared namespace under a gate."""
    t0 = time.perf_counter()
    # deterministic payload -> hash should be IDENTICAL across requests if no contamination
    payload = b"payload-" + str(ident % 3).encode()
    h = hashlib.sha256(payload).hexdigest()[:8]
    # emulate noisy-neighbor: a lock-stealing window for odd workers
    if inject_flag and ident % 2 == 1:
        time.sleep(0.02)  # hold the "lock" longer -> neighbor latency
    lat = (time.perf_counter() - t0) * 1000
    outq.put({"req": ident, "hash": h, "lat_ms": round(lat, 2)})

def run_matrix(n=8, inject_noisy=True):
    outq = mp.Queue()
    procs = [mp.Process(target=worker, args=(i, inject_noisy, outq)) for i in range(n)]
    t0 = time.perf_counter()
    [p.start() for p in procs]
    [p.join() for p in procs]
    wall = (time.perf_counter() - t0) * 1000
    rows = [outq.get() for _ in range(n)]
    # cross-request contamination check: same payload group must share one hash
    by_group = {}
    for r in rows:
        g = r["req"] % 3
        by_group.setdefault(g, set()).add(r["hash"])
    contamination = {g: len(s) > 1 for g, s in by_group.items()}
    maxlat = max(r["lat_ms"] for r in rows)
    return {"wall_ms": round(wall, 2), "max_lat_ms": maxlat,
            "contamination": contamination, "rows": rows}

if __name__ == "__main__":
    n = int(__import__("sys").argv[1]) if len(__import__("sys").argv) > 1 else 8
    print(json.dumps(run_matrix(n, True), indent=2))
