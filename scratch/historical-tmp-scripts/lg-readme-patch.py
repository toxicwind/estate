#!/usr/bin/env python3
"""Insert race_exec README row after the squawk row (idempotent)."""
import io

p = "/tmp/lg-wt/hatch/bin/README.md"
s = io.open(p, encoding="utf-8").read()
anchor = "| `agent-reaper` |"
row = ("| `race_exec` | Bridge auto-racer: races the WS vs HTTPS exec lanes "
       "on readiness probes (first-valid-wins, fail-fast ceilings, abandoned "
       "loser threads). Default dispatch-race dispatches on exactly one lane "
       "(never double-executes); `--idempotent` runs a true full race. "
       "Bounded-semaphore dispatch-gating (default 4) so bursts never flood "
       "the bridge; fsync'd JSONL ledger. Live cell copy: "
       "`~/workspace/awrawr-bridge/race_exec.py`. |\n"
       "| `tests/test_race_exec.py` | Unit tests for race_exec (13 pass): "
       "probe-race winners, down-flag/degraded fast paths, both-down raise, "
       "full-race first-valid, no-double-dispatch contract, gate limit + "
       "fail-fast timeout, pre-dispatch fallback, fsync'd ledger, bounded "
       "race with a hung lane. |\n")
if "| `race_exec` |" not in s:
    assert anchor in s, "anchor row missing"
    s = s.replace(anchor, row + anchor, 1)
    io.open(p, "w", encoding="utf-8").write(s)
    print("README row inserted")
else:
    print("README row already present")
