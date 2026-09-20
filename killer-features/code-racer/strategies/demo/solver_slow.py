#!/usr/bin/env python3
"""demo-slow: correct solution, but sleeps 3s first (latency ordering probe)."""
import sys
import time
from pathlib import Path

SRC = '''def two_sum(nums, target):
    seen = {}
    for i, v in enumerate(nums):
        need = target - v
        if need in seen:
            return [seen[need], i]
        seen[v] = i
    raise ValueError("no pair")
'''

time.sleep(3)
outdir = Path(sys.argv[1])
outdir.mkdir(parents=True, exist_ok=True)
(outdir / "solution.py").write_text(SRC)
print("demo-slow: solution written")
