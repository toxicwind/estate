#!/usr/bin/env python3
"""tern 2026-09-21: bidder.py ceiling buffer fix.

The oracle's exec deadline is assign_ts + timeout_ms/1000. The bidder's
subprocess ceiling was min(timeout_ms/1000, RALPH_CAP_S) -- but the
bidder starts the subprocess AFTER assignment (bid acceptance, workdir
setup), so the oracle's deadline ALWAYS fires first when
timeout_ms/1000 < RALPH_CAP_S. The TimeoutExpired handler (with the
partial-evidence preservation) could never fire.

Fix: subtract a post buffer so the subprocess times out BEFORE the
oracle's deadline, giving the bidder time to preserve evidence and
post the partial result.
"""
P = "/home/toxic/sovereign/agents/oracle-market/bin/bidder.py"
src = open(P, encoding="utf-8").read()

old = "        ceiling = min(timeout_ms / 1000.0, RALPH_CAP_S)\n"
new = ("        # 2026-09-21 (tern): the oracle's exec deadline is\n"
       "        # assign_ts + timeout_ms/1000, but the bidder starts the\n"
       "        # subprocess after assignment. Without a buffer the oracle\n"
       "        # always wins the race and the TimeoutExpired handler (with\n"
       "        # partial-evidence preservation) can never fire. Leave room\n"
       "        # to preserve evidence and post the partial result.\n"
       "        ceiling = max(10.0, min(timeout_ms / 1000.0, RALPH_CAP_S)\n"
       "                    - RALPH_POST_BUFFER_S)\n")
assert src.count(old) == 1, "ceiling anchor"
src = src.replace(old, new)

old2 = "RALPH_CAP_S = 1740  # 29 min ceiling: Super Ralph runs are slow (~11 min\n"
assert old2 in src, "cap anchor"
src = src.replace(
    "OUT_CAP = 8000\nERR_CAP = 2000\nPARTIAL_CAP = 65536",
    "OUT_CAP = 8000\nERR_CAP = 2000\nPARTIAL_CAP = 65536\n"
    "RALPH_POST_BUFFER_S = 30.0  # time to preserve evidence + post result\n"
    "                             # before the oracle's exec deadline",
)

with open(P, "w", encoding="utf-8") as f:
    f.write(src)
print("ceiling buffer patched OK")
