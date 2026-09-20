#!/usr/bin/env python3
"""Experiment: the Clopper-Pearson abstention guarantee behaves as specified.

Checks (deterministic, no model calls):
  1. Cold start (no history): only unanimous high-confidence emits; a
     0.62/0.58 split escalates.
  2. Strong history (38/40 correct): CP lower bound 0.832 >= 0.80 -> emits.
  2b. Same 95% rate at n=20 (19/20): CP lower bound 0.751 < 0.80 ->
      correctly ESCALATES (finite-sample honesty: n=20 cannot
      guarantee 80% at 95% confidence).
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

# 5. cold-start unanimity/confidence threshold sweep. The bar must satisfy
#    three properties:
#    (a) emits the canonical unanimous extreme (0.93, 0.95);
#    (b) refuses the near-miss (0.85 posterior, 0.88 conf) -- confidence
#        below the unanimity proxy must not emit;
#    (c) refuses (0.82 posterior, 0.93 conf) -- posterior below the AUTO
#        tier's own 0.85 bar must not emit at cold start, or the gate would
#        be looser than the tier ladder it serves.
#    The sweep maps the candidate space. Two candidates satisfy all three;
#    the tie-break is principled, not empirical: the posterior bar must
#    equal AUTO_P so the gate can never emit what the tier ladder would
#    not auto-resolve. The rejected qualifier (0.95, 0.90) would withhold
#    verdicts at posteriors [0.85, 0.90) that the AUTO tier itself emits --
#    a gate/ladder contradiction. The confidence bar 0.90 matches the
#    unanimity confidence in escalation.route. Emit fractions are reported
#    for transparency (fail-closed prefers the smaller emit region).
if os.path.exists(cal.HISTORY_PATH):
    os.remove(cal.HISTORY_PATH)
posteriors = [0.55, 0.62, 0.70, 0.75, 0.80, 0.82, 0.85, 0.88, 0.90, 0.95]
confidences = [0.50, 0.60, 0.70, 0.80, 0.83, 0.85, 0.88, 0.90, 0.93, 0.95]
candidates = [(0.80, 0.80), (0.85, 0.85), (0.90, 0.85),
              (0.90, 0.90), (0.95, 0.90)]


def _emit(p, c, sb, pb):
    d, _ = engine.abstention_gate(p, c, struct_bar=sb, post_bar=pb)
    return d == "emit"


rows = []
for sb, pb in candidates:
    grid_emits = sum(_emit(p, c, sb, pb)
                     for p in posteriors for c in confidences)
    frac = grid_emits / (len(posteriors) * len(confidences))
    canon = _emit(0.93, 0.95, sb, pb)
    nearmiss = _emit(0.85, 0.88, sb, pb)
    belowauto = _emit(0.82, 0.93, sb, pb)
    rows.append((sb, pb, frac, canon, nearmiss, belowauto))
    print("sweep struct>=%.2f post>=%.2f: emit-frac=%.3f canon=%s "
          "near-miss=%s below-auto=%s"
          % (sb, pb, frac, canon, nearmiss, belowauto))

qualifiers = [r for r in rows
              if r[3] and not r[4] and not r[5]]
check("selected bar satisfies all three properties",
      (engine.COLD_STRUCT_BAR, engine.COLD_POSTERIOR_BAR, True, False, False)
      in [(r[0], r[1], r[3], r[4], r[5]) for r in rows],
      str(rows))
sel = (engine.COLD_STRUCT_BAR, engine.COLD_POSTERIOR_BAR)
check("selected bar posterior bar == AUTO_P (tier-ladder consistency)",
      sel[1] == engine.AUTO_P, "post_bar=%.2f AUTO_P=%.2f" % (sel[1], engine.AUTO_P))
check("selected bar confidence bar == unanimity confidence (0.90)",
      sel[0] == 0.90, "struct_bar=%.2f" % sel[0])
for r in qualifiers:
    if (r[0], r[1]) != sel:
        check("rejected qualifier documented: (%.2f,%.2f) contradicts ladder"
              % (r[0], r[1]),
              r[1] > engine.AUTO_P,
              "withholds posteriors [%.2f,%.2f) the AUTO tier emits"
              % (engine.AUTO_P, r[1]))
print("qualifiers: %s" % [(r[0], r[1]) for r in qualifiers])

print("PASS %d FAIL %d" % (PASS, FAIL))
sys.exit(1 if FAIL else 0)
