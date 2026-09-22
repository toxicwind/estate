#!/usr/bin/env python3
"""Nightjar lane: add bounded jittered backoff before same-alias judge retries.

Applies a 3-effective-line change to
/home/toxic/sovereign/agents/oracle-market/bin/oracle_ask.py:

  1. import random (one line)
  2. time.sleep(random.uniform(0.25, 1.0)) before each same-alias
     attempt-2 retry in _resilient_judge (two sites, one line each + comment)

Rationale (papers/patterns): RetryGuard (arXiv 2511.23278) shows naive
immediate retries become self-inflicted retry storms; LiteLLM's router adds
jitter to every backoff (utils._calculate_retry_after); resilience4j treats
un-jittered re-rolls as a storm risk. The different-provider attempt-2 stays
immediate (fresh path, hedging-like); only re-rolling the SAME alias waits,
bounded at 1.0s — negligible against the 90s per-try timeout and 240s budget.
Revert: diff is trivially reversible; backup written next to the file.
"""
import os
import re
import shutil
import sys

PATH = "/home/toxic/sovereign/agents/oracle-market/bin/oracle_ask.py"
BAK = PATH + ".bak-nightjar-jitter"

with open(PATH) as f:
    src = f.read()

orig = src

# 1. import random, once
if "\nimport random\n" not in src:
    src = src.replace("\nimport re\n", "\nimport re\nimport random\n", 1)

# 2. jittered backoff before BOTH same-alias attempt-2 retries
#    (provider-class branch with no alt provider; non-provider-class branch)
pat = re.compile(r"(?m)^([ ]*)jp = _call\(model, min\(timeout_s, 60\.0\), 2\)$")
def repl(m):
    ind = m.group(1)
    return (
        ind + "# jittered backoff before re-rolling the SAME alias:\n"
        + ind + "# immediate re-rolls of a flaky alias self-inflict retry storms\n"
        + ind + "# (RetryGuard 2511.23278; LiteLLM _calculate_retry_after; resilience4j).\n"
        + ind + "time.sleep(random.uniform(0.25, 1.0))\n"
        + m.group(0)
    )
src, n = pat.subn(repl, src)

assert src.count("import random") >= 1, "import random not applied"
assert n == 2, "expected exactly 2 same-alias retry sites, found %d" % n

changed = [i + 1 for i, (a, b) in enumerate(zip(orig.splitlines(), src.splitlines()))
           if a != b]
print("retry sites patched: %d" % n)

shutil.copy2(PATH, BAK)
with open(PATH, "w") as f:
    f.write(src)

print("wrote %s (backup %s)" % (PATH, BAK))

# 3. syntax check the result
import py_compile
py_compile.compile(PATH, doraise=True)
print("py_compile OK")

# 4. show the patched hunks for the receipt
out = []
lines = src.splitlines()
for i, line in enumerate(lines):
    if "time.sleep(random.uniform(0.25, 1.0))" in line:
        out.extend("  %d: %s" % (j + 1, lines[j]) for j in range(max(0, i - 3), min(len(lines), i + 2)))
print("\n".join(out))
