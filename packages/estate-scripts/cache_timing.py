#!/usr/bin/env python3
"""
cache_timing.py: Cache side-channel timing probe (educational).
"""
import time, os

def probe(secret_idx=42, iterations=1000):
    ARRAY_SIZE = 256 * 4096
    arr = bytearray(ARRAY_SIZE)
    for i in range(256):
        arr[i * 4096] = i

    times = [[] for _ in range(256)]
    for _ in range(iterations):
        # Evict
        for j in range(0, ARRAY_SIZE, 4096):
            arr[j] = (arr[j] + 1) % 256
        # Access secret
        arr[secret_idx * 4096] = secret_idx
        # Measure
        for i in range(256):
            t0 = time.perf_counter_ns()
            _ = arr[i * 4096]
            t1 = time.perf_counter_ns()
            times[i].append(t1 - t0)

    avg = [(i, sum(times[i])/len(times[i])) for i in range(256)]
    avg.sort(key=lambda x: x[1])
    return avg

if __name__ == "__main__":
    results = probe(42, 500)
    print("Top 10 fastest (secret=42):")
    for idx, t in results[:10]:
        marker = " <<< SECRET" if idx == 42 else ""
        print(f"  idx={idx:3d}: {t:8.1f} ns{marker}")
