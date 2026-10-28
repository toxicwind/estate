#!/usr/bin/env python3
"""demo-broken: writes an incorrect solution (must never win)."""
import sys
from pathlib import Path

SRC = '''def two_sum(nums, target):
    return [0, 0]
'''

outdir = Path(sys.argv[1])
outdir.mkdir(parents=True, exist_ok=True)
(outdir / "solution.py").write_text(SRC)
print("demo-broken: solution written")
