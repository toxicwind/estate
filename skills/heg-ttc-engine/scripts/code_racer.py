#!/usr/bin/env python3
"""
Universal Code Racer Engine for Autonomous SWE Agents
Enforces empirical route selection and candidate patch benchmarking.
"""
import time
import gc
import statistics
import sys
from typing import Dict, Callable, Any, List

class CodeRacer:
    def __init__(self, warmup_runs: int = 5, test_runs: int = 30):
        self.warmup_runs = warmup_runs
        self.test_runs = test_runs

    def race(self, candidates: Dict[str, Callable[[], Any]]) -> List[Dict[str, Any]]:
        results = []
        for name, func in candidates.items():
            for _ in range(self.warmup_runs):
                func()
            timings_ns = []
            gc.disable()
            try:
                for _ in range(self.test_runs):
                    t0 = time.perf_counter_ns()
                    res = func()
                    t1 = time.perf_counter_ns()
                    timings_ns.append(t1 - t0)
            finally:
                gc.enable()
                gc.collect()
            timings_ms = [t / 1_000_000.0 for t in timings_ns]
            results.append({
                "name": name,
                "median_ms": statistics.median(timings_ms),
                "min_ms": min(timings_ms),
                "passed": bool(res)
            })
        results.sort(key=lambda x: x["median_ms"])
        fastest = results[0]["median_ms"]
        for rank, r in enumerate(results, 1):
            r["rank"] = rank
            r["speedup"] = results[-1]["median_ms"] / r["median_ms"] if r["median_ms"] > 0 else float('inf')
        return results

if __name__ == "__main__":
    print("[code_racer] CodeRacer module active.")
