#!/usr/bin/env python3
"""Deterministic unit tests for the Oracle core. No model calls, no network.

Run: python3 bench/test_core.py
Covers: bayes guards, calibration math, engine pooling/gates,
evidence partitioning, escalation routing, sizing invariants.
"""
import math
import os
import sys

BIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bin")
sys.path.insert(0, BIN)
os.environ["ORACLE_WORK"] = "/tmp/oracle-test-work"

import bayes
import calibration as cal
import engine
import evidence as ev
import escalation
import sizing

PASS = 0
FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print("FAIL %s %s" % (name, detail))


def approx(a, b, tol=1e-6):
    return abs(a - b) <= tol


# ---- bayes: Raven guards ----
check("llr clamp", bayes.clamp(5.0, -2.0, 2.0) == 2.0 and
      bayes.clamp(-5.0, -2.0, 2.0) == -2.0 and bayes.MAX_ABS_LLR == 2.0)
check("stance flip", bayes.effective_llr("supports_no", 1.5) == -1.5)
check("stance neutral", bayes.effective_llr("neutral", 1.5) == 0.0)
check("unverified soft clamp", bayes.clamp_unverified(1.9) == 0.2)
check("credibility cap medium", bayes.credibility_cap("medium", 1.9) == 0.8)
check("credibility cap high", bayes.credibility_cap("high", 1.9) == 1.9)
check("reflection clamp", bayes.clamp_reflection(2.0) == 1.0)
check("prob floor/ceil", bayes.PROB_FLOOR == 0.01 and bayes.PROB_CEIL == 0.99)
p, steps, pinned = bayes.apply_llrs(0.5, [2.0] * 6)
check("apply pins", pinned == "ceil" and p == 0.99, "p=%s pinned=%s" % (p, pinned))
check("logit roundtrip", approx(bayes.inv_logit(bayes.logit(0.3)), 0.3))
f = bayes.cluster_factors(["a", "a", "b"], [1.0, 1.0, 1.0], {"a": 2})
check("cluster discount", f[0] < 1.0 and f[1] < 1.0 and f[2] == 1.0, str(f))
check("confirmation ratio", approx(bayes.confirmation_ratio(0.6, [1.0, 1.0, -1.0]),
                                  2.0 / 3.0))
check("confirmation ratio none at 0.5",
      bayes.confirmation_ratio(0.5, [1.0]) is None)

# ---- calibration math ----
lo, hi = cal.clopper_pearson(8, 8, 0.05)
check("CP 8/8 lower", approx(lo, 0.6306, 1e-3), "lo=%s" % lo)
check("CP 0/8 upper", cal.clopper_pearson(0, 8, 0.05)[1] < 0.4)
check("CP symmetric 4/8", approx(cal.clopper_pearson(4, 8, 0.05)[0],
                                 1 - cal.clopper_pearson(4, 8, 0.05)[1], 1e-9))
check("bias point", approx(cal.bias_corrected_point(0.8, 0.9, 0.9), 0.875))
bc_lo, bc_hi = cal.bias_corrected_ci(0.8, 0.9, 0.9, 50, 100, 100)
check("bias CI ordered", bc_lo <= 0.875 <= bc_hi, "%s %s" % (bc_lo, bc_hi))
check("norm_ppf", approx(cal.norm_ppf(0.5), 0.0, 1e-9))
check("norm roundtrip", approx(cal.norm_cdf(cal.norm_ppf(0.7)), 0.7, 1e-9))
check("nll sane", cal.nll([0.9, 0.1], [1, 0]) < cal.nll([0.5, 0.5], [1, 0]))
g = cal.RefusalGate()
g.set("a", "PASS", "ok"); g.set("b", "NOT_CHECKED", "later")
check("gate strict: NOT_CHECKED blocks ok()", not g.ok() and g.failures() == {},
      "NOT_CHECKED must never pass silently")
check("limitations line", "NOT_CHECKED" in g.limitations_line())
budget = cal.label_budget(100, {"j1": 1.0, "j2": 4.0})
check("sqrt budget", budget["j2"] > budget["j1"] and
      abs(sum(budget.values()) - 100) < 1e-9, str(budget))

# ---- engine ----
jp = [engine.JudgePosterior("a", 0.7), engine.JudgePosterior("b", 0.8)]
post, contrib = engine.pooled_posterior(0.5, jp)
check("pooled", approx(post, 0.9032, 1e-3), "post=%s" % post)
check("pooled contrib", len(contrib) == 2)
refused = [engine.JudgePosterior("a", 0.7, refused=True)]
post2, _ = engine.pooled_posterior(0.5, refused)
check("refused ignored", post2 == 0.5)
feats = engine.disagreement_features(jp)
check("struct conf range", 0.0 <= feats["confidence"] <= 1.0)
v = engine.build_verdict({"binary_question": "Q?", "base_rate_prior": 0.5,
                          "question_id": "t1", "resolution_criteria": "c"},
                         jp)
check("verdict shape", v["status"] in ("verdict", "escalate") and
      "verdict_sha256" in v and "gate" in v)
check("engine owns numbers", 0.01 <= v["probability"] <= 0.99)
flags = engine.check_canaries(jp, [{"id": "c1", "answer": True}])
jp[0].__dict__["canary_scores"] = {"c1": 0.02}  # confidently anti-answer
flags = engine.check_canaries(jp, [{"id": "c1", "answer": True}])
check("canary gaming flag", len(flags) == 1 and
      flags[0]["pattern"] == "confident_anti_answer", str(flags))

# ---- evidence ----
items = [{"id": str(i), "text": "e%d" % i, "relevance": 1.0 - i / 20.0,
          "source": "s"} for i in range(20)]
part = ev.partition_evidence(items, 4)
priv_ids = [e["id"] for grp in part["private"] for e in grp]
check("partition disjoint", len(set(priv_ids)) == len(priv_ids))
check("partition covers", len(priv_ids) + len(part["public"]) == 20)
c = ev.verify_claim_urls({"urls": ["u1"]}, ["u1", "u2"])
check("url verified", c["verified"])
c2 = ev.verify_claim_urls({"urls": ["u9"]}, ["u1", "u2"])
check("url fabrication", not c2["verified"])
post3, steps3, rep = ev.apply_claims(0.5, [
    {"text": "t1", "stance": "supports_yes", "llr": 5.0,
     "cluster_id": "x", "credibility": "low", "urls": ["u1"]}], None, ["u1"])
check("claim guards compose", steps3[0]["llr"] == 0.25 and
      "credibility_cap" in steps3[0]["guards"], str(steps3[0]))

# ---- escalation ----
tier, why = escalation.route([0.9, 0.92, 0.88], 0.95, True)
check("auto tier", tier == "AUTO", tier)
tier2, _ = escalation.route([0.9, 0.3, 0.6], 0.4, True)
check("debate tier", tier2 == "DEBATE", tier2)
tier3, _ = escalation.route([], 0.5, False)
check("human tier empty", tier3 == "HUMAN", tier3)
tier4, _ = escalation.route([0.7, 0.75], 0.7, True, invariant_ok=False)
check("invariant violation debates", tier4 == "DEBATE", tier4)
mock = lambda prompt: {"posterior": 0.6, "concession": None}
d = escalation.debate_tier("Q?", "crit", "ev", mock, k=2, max_rounds=2)
check("debate budgeted", d["rounds"] <= 2 and 0.01 <= d["posterior"] <= 0.99)

# ---- sizing ----
check("wang 0.5 ~ 0.57", approx(sizing.wang_fair_value(0.5), 0.5726, 1e-3))
check("kelly no edge", sizing.kelly_fraction(0.5, 0.5) == 0.0)
check("kelly edge", sizing.kelly_fraction(0.65, 0.57) > 0)
s = sizing.size_stake(0.65, 0.57, 1000)
check("size action", s["action"] == "bet_yes" and s["stake"] <= 100,
      str(s))
s2 = sizing.size_stake(0.55, 0.54, 1000)
check("size no bet", s2["action"] == "no_bet", str(s2))
viol = sizing.invariant_check([
    {"id": "a", "p": 0.6, "group": "g1", "group_kind": "exclusive"},
    {"id": "b", "p": 0.6, "group": "g1", "group_kind": "exclusive"}])
check("exclusivity violation", len(viol) == 1 and
      viol[0]["invariant"] == "exclusivity")
viol2 = sizing.invariant_check([
    {"id": "a", "p": 0.8, "implies": "b"},
    {"id": "b", "p": 0.5}])
check("implication violation", len(viol2) == 1)

print("PASS %d FAIL %d" % (PASS, FAIL))
sys.exit(1 if FAIL else 0)
