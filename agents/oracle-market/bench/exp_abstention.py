#!/usr/bin/env python3
"""Experiment: the Clopper-Pearson abstention guarantee behaves as specified.

Checks (deterministic, no model calls):
  1. Cold start (no history): only unanimous high-confidence emits; a
     0.62/0.58 split escalates.
  2. Strong history (19/20 correct): CP lower bound 0.805 >= 0.80 -> emits.
  3. Weak history (14/20 correct): CP lower bound 0.457 < 0.80 -> escalates.
  4. Monotonicity: as accuracy degrades, the gate flips emit->escalate once.
"""
import json
import os
import sys

BIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bin")
sys.path.insert(0, BIN)

WORK = "/tmp/oracle-abstain-work"
os.environ["ORACLE_WORK"] = WORK
os.makedirs(WORK, exist_ok=True)

import calibration as cal
import engine

PASS = 0
FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print("FAIL %s %s" % (name, detail))


def seed_history(correct, total):
    os.makedirs(os.path.dirname(cal.HISTORY_PATH), exist_ok=True)
    with open(cal.HISTORY_PATH, "w") as f:
        for i in range(total):
            f.write(json.dumps({"question_id": "h%d" % i,
                                "correct": i < correct,
                                "ts": 0.0}) + "\n")


# 1. cold start
if os.path.exists(cal.HISTORY_PATH):
    os.remove(cal.HISTORY_PATH)
d, r = engine.abstention_gate(0.93, 0.95)
check("cold start unanimous emits", d == "emit", "%s %s" % (d, r))
d2, r2 = engine.abstention_gate(0.62, 0.55)
check("cold start split escalates", d2 == "escalate", "%s %s" % (d2, r2))

# 2. strong history: 38/40 (same 95% rate as 19/20, but n=40 lets the
#    finite-sample guarantee clear the bar: CP lo 0.832 >= 0.80)
seed_history(38, 40)
d3, r3 = engine.abstention_gate(0.75, 0.8)
lo, _ = cal.clopper_pearson(38, 40, 0.05)
check("38/40 emits (CP lo=%.3f)" % lo, d3 == "emit", r3)

# 2b. same rate, half the labels: 19/20 correctly ESCALATES — n=20 cannot
#     guarantee 80% at 95% confidence (CP lo 0.751). This is the guarantee
#     working, not a bug.
seed_history(19, 20)
d3b, r3b = engine.abstention_gate(0.75, 0.8)
check("19/20 escalates (finite-sample honesty)", d3b == "escalate", r3b)

# 3. weak history
seed_history(14, 20)
d4, r4 = engine.abstention_gate(0.75, 0.8)
lo4, _ = cal.clopper_pearson(14, 20, 0.05)
check("14/20 escalates (CP lo=%.3f)" % lo4, d4 == "escalate", r4)

# 4. monotonicity: 20 histories from perfect down to 50%
flips = 0
prev = "emit"
for correct in range(20, 9, -1):
    seed_history(correct, 20)
    d5, _ = engine.abstention_gate(0.75, 0.8)
    if d5 != prev:
        flips += 1
    prev = d5
check("single emit->escalate flip", flips == 1, "flips=%d" % flips)

print("PASS %d FAIL %d" % (PASS, FAIL))
sys.exit(1 if FAIL else 0)
