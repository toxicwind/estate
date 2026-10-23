#!/usr/bin/env python3
"""GRIEF-style timed multi-request trace matrix for DoH.
Issues N concurrent DoH lookups (via the local discrepancy path) to expose
cross-request contamination (mismatched verdict for same domain), noisy
neighbor (latency spikes), and silent corruption. Structure-only self-contained.
"""
import multiprocessing as mp, time, json, subprocess, os, sys

def lookup(ident, outq):
    t0 = time.perf_counter()
    # consistent domain+type => consistent verdict expected unless contamination
    r = subprocess.run("python3 doh_probe.py example.com A --local", shell=True,
                       capture_output=True, text=True, timeout=30)
    lat = (time.perf_counter()-t0)*1000
    try:
        v = json.loads(r.stdout).get("vjTrigger")
    except Exception:
        v = "PARSE_ERR"
    outq.put({"req": ident, "verdict": v, "lat_ms": round(lat, 2)})

def run_matrix(n=8):
    outq, procs = mp.Queue(), []
    for i in range(n):
        p = mp.Process(target=lookup, args=(i, outq)); p.start(); procs.append(p)
    t0 = time.perf_counter()
    for p in procs: p.join()
    wall = (time.perf_counter()-t0)*1000
    rows = [outq.get() for _ in range(n)]
    verdicts = {r["verdict"] for r in rows}
    lat = [r["lat_ms"] for r in rows]
    return {"wall_ms": round(wall,2), "unique_verdicts": sorted(verdicts),
            "max_lat_ms": round(max(lat),2), "p95_lat_ms": round(sorted(lat)[int(n*0.95)-1],2) if n else None,
            "contamination": len(verdicts) > 1}

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv)>1 else 8
    print(json.dumps(run_matrix(n), indent=2))
