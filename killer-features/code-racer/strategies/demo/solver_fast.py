#!/usr/bin/env python3
"""demo-fast: writes a correct O(n) two_sum solution immediately."""
import sys
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

outdir = Path(sys.argv[1])
outdir.mkdir(parents=True, exist_ok=True)
(outdir / "solution.py").write_text(SRC)
print("demo-fast: solution written")
