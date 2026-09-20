#!/usr/bin/env python3
"""Deterministic aggregation engine — the Oracle's constitutional core.

CONSTITUTIONAL RULE: the deterministic engine owns every number it emits —
verdicts, probabilities, confidence, payouts. LLM judges are advisors
producing structured, attributable inputs (posteriors, per-claim LLRs).
No LLM output ever bypasses this engine. The engine's acceptance checks
outrank every judge. (Borrow: PROCTOR arXiv:2609.02246; Raven-Agent
arXiv:2607.03015; see docs/BORROWS.md.)

Layer 3 per the research design:
  * pooled posterior via product-of-posteriors (Blackwell bound,
    arXiv:2605.06028): each judge reports a posterior; the engine combines
    in log-odds with calibration weights x datasheet reliability.
  * confidence from DISAGREEMENT STRUCTURE (DiscoUQ, arXiv:2603.20975) —
    evidence overlap, stance divergence, confidence spread — never raw
    vote margins.
  * every verdict ships bias-corrected point estimate + CI (judge-reporting
    math) and a limitations line (CJE-style NOT_CHECKED).
  * abstention gate with finite-sample Clopper-Pearson guarantee
    (arXiv:2608.17994): below-threshold verdicts escalate, never emitted.
  * canary checks: seeded known-answer questions where a perfect-but-wrong
    pattern exposes gaming (feeds stake-and-slash evidence).
"""
import hashlib
import json
import math
import os
import time

import bayes
import calibration as cal

WORK = os.environ.get("ORACLE_WORK", "/home/toxic/sovereign/agents/oracle-market/work")
VERDICT_LEDGER = os.path.join(WORK, "verdicts.jsonl")
CANARY_PATH = os.path.join(WORK, "canaries.json")

# Abstention-gate defaults (proven values documented in docs/oracle-core.md).
GATE_ALPHA = 0.05          # FDR target among emitted verdicts
GATE_MIN_HISTORY = 8       # labeled accepted verdicts before the gate trusts history
GATE_MIN_ACCURACY = 0.80   # CP lower bound on accepted-set accuracy to emit
AUTO_P = 0.85              # unanimity auto-resolve posterior bar


class JudgePosterior:
    def __init__(self, judge_id, posterior, cal_weight=1.0, reliability=1.0,
                 verbal_conf=None, claims=None, refused=False):
        self.judge_id = judge_id
        self.posterior = min(0.999, max(0.001, float(posterior)))
        self.cal_weight = float(cal_weight)
        self.reliability = float(reliability)
        self.verbal_conf = verbal_conf
        self.claims = claims or []   # atomic claims: {cluster_id, stance, ...}
        self.refused = refused

    @property
    def weight(self):
        return self.cal_weight * self.reliability


def pooled_posterior(prior, judges):
    """Product-of-posteriors in log-odds space (Blackwell bound).

    L = logit(prior) + sum_i w_i * logit(calibrated_posterior_i).
    Judges advise; the engine decides. Refused judges contribute nothing.
    """
    live = [j for j in judges if not j.refused]
    if not live:
        return prior, []
    lo = bayes.logit(prior)
    contrib = []
    for j in live:
        c = j.weight * bayes.logit(j.posterior)
        lo += c
        contrib.append({"judge": j.judge_id, "weight": j.weight,
                        "posterior": j.posterior, "logit_contrib": c})
    post = bayes.inv_logit(lo)
    return min(bayes.PROB_CEIL, max(bayes.PROB_FLOOR, post)), contrib


def disagreement_features(judges):
    """DiscoUQ-lite: confidence from disagreement STRUCTURE, not vote margins.
    Features: evidence overlap (Jaccard of cluster_ids), stance divergence,
    posterior spread. Returns dict with a structural confidence in [0,1]."""
    live = [j for j in judges if not j.refused]
    if len(live) < 2:
        return {"confidence": 0.5, "note": "single judge — no structure"}
    posts = [j.posterior for j in live]
    mean = sum(posts) / len(posts)
    spread = math.sqrt(sum((p - mean) ** 2 for p in posts) / len(posts))
    # evidence overlap: Jaccard over cluster id sets
    sets = [set(c.get("cluster_id", "") for c in j.claims if c.get("cluster_id"))
            for j in live]
    unions = set().union(*sets) if sets else set()
    pairwise = []
    for a in range(len(sets)):
        for b in range(a + 1, len(sets)):
            u = sets[a] | sets[b]
            pairwise.append(len(sets[a] & sets[b]) / len(u) if u else 1.0)
    overlap = sum(pairwise) / len(pairwise) if pairwise else 1.0
    # stance divergence: fraction of judges on the minority side of 0.5
    yes = sum(1 for p in posts if p >= 0.5)
    divergence = min(yes, len(posts) - yes) / len(posts)
    # structural confidence: high when judges agree on INDEPENDENT evidence
    # (low overlap + low spread), low when they herd on the same evidence
    # (high overlap) or genuinely diverge (high spread/divergence).
    independence = 1.0 - overlap
    agreement = 1.0 - min(1.0, spread * 4.0)
    confidence = min(1.0, max(0.0,
                              0.5 * agreement + 0.3 * independence
                              + 0.2 * (1.0 - divergence * 2.0)))
    return {"confidence": confidence, "spread": spread,
            "evidence_overlap": overlap, "stance_divergence": divergence,
            "n_judges": len(live)}


def _accepted_history():
    rows = []
    if os.path.exists(cal.HISTORY_PATH):
        with open(cal.HISTORY_PATH) as f:
            for line in f:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    return rows


def abstention_gate(posterior, struct_conf, alpha=GATE_ALPHA):
    """Finite-sample abstention gate (Judge/Retrieve/Abstain pattern).

    Emits only if the Clopper-Pearson LOWER bound on the accepted set's
    historical accuracy stays above GATE_MIN_ACCURACY. Cold start (too
    little history): emit only unanimous high-confidence verdicts.
    Below threshold -> ("escalate", reason), never emitted.
    """
    hist = [r for r in _accepted_history() if "correct" in r]
    if len(hist) < GATE_MIN_HISTORY:
        # cold start: conservative — unanimity bar only
        if struct_conf >= 0.90 and (posterior >= AUTO_P or posterior <= 1 - AUTO_P):
            return ("emit", "cold-start unanimity bar")
        return ("escalate", "cold start: insufficient accepted history "
                "(%d<%d)" % (len(hist), GATE_MIN_HISTORY))
    k = sum(1 for r in hist if r["correct"])
    lo, _hi = cal.clopper_pearson(k, len(hist), alpha)
    if lo >= GATE_MIN_ACCURACY:
        return ("emit", "CP lower bound on accepted accuracy %.3f >= %.2f "
                % (lo, GATE_MIN_ACCURACY))
    return ("escalate", "CP lower bound %.3f < %.2f on %d accepted" %
            (lo, GATE_MIN_ACCURACY, len(hist)))


def check_canaries(judges, canaries=None):
    """PROCTOR-style canary pattern: seeded known-answer questions where a
    perfect-but-wrong pattern exposes gaming. Returns flags list; a flag is
    stake-and-slash evidence, not an auto-slash."""
    if canaries is None:
        if os.path.exists(CANARY_PATH):
            with open(CANARY_PATH) as f:
                canaries = json.load(f)
        else:
            canaries = []
    flags = []
    for j in judges:
        if j.refused:
            continue
        for c in canaries:
            ans = c.get("answer")
            # judge posterior on the canary is expected in j.canary_scores
            got = (j.__dict__.get("canary_scores") or {}).get(c.get("id"))
            if got is None or ans is None:
                continue
            wrong = (got >= 0.5) != bool(ans)
            if wrong and abs(got - (1.0 - ans)) < 0.05:
                # confidently wrong in exactly the anti-answer direction:
                # the gaming signature (perfect-but-wrong pattern)
                flags.append({"judge": j.judge_id, "canary": c.get("id"),
                              "pattern": "confident_anti_answer",
                              "posterior": got})
    return flags


def build_verdict(question_record, judges, prior=None, alpha=GATE_ALPHA):
    """Full verdict pipeline. Returns the verdict dict; status is one of
    'verdict' | 'escalate' | 'refused'. The engine owns every number."""
    if question_record.get("status") == "refused":
        return {"status": "refused", "question_id": None,
                "clarification_request":
                question_record.get("clarification_request")}
    prior = prior if prior is not None else question_record.get(
        "base_rate_prior", 0.5)
    loop = cal.CalibrationLoop()
    # apply deployed calibrators to raw judge posteriors
    calibrated = []
    for j in judges:
        raw = j.posterior
        p = loop.apply(j.judge_id, raw)
        calibrated.append(JudgePosterior(
            j.judge_id, p, j.cal_weight, j.reliability,
            j.verbal_conf, j.claims, j.refused))
        if p != raw:
            pass
    post, contrib = pooled_posterior(prior, calibrated)
    feats = disagreement_features(calibrated)
    # bias-corrected reporting (judge-reporting math on the panel as an instrument)
    live = [j for j in calibrated if not j.refused]
    agree = [1 if (j.posterior >= 0.5) == (post >= 0.5) else 0 for j in live]
    p_agree = sum(agree) / len(agree) if agree else 0.5
    n = len(agree)
    bc_point = cal.bias_corrected_point(p_agree, 0.9, 0.9)
    bc_lo, bc_hi = cal.bias_corrected_ci(p_agree, 0.9, 0.9, max(n, 1), 20, 20)
    gate = cal.RefusalGate()
    canary_flags = check_canaries(calibrated)
    gate.set("canary", "PASS" if not canary_flags else "FAIL",
             "%d gaming flags" % len(canary_flags))
    gate.set("panel_nonempty", "PASS" if live else "FAIL",
             "%d live judges" % len(live))
    decision, reason = abstention_gate(post, feats["confidence"], alpha)
    gate.set("abstention", "PASS" if decision == "emit" else "FAIL", reason)
    gate.set("drift", "NOT_CHECKED", "outer loop not yet run")
    verdict = {
        "status": "verdict" if decision == "emit" else "escalate",
        "question_id": question_record.get("question_id"),
        "binary_question": question_record.get("binary_question"),
        "probability": post,
        "bias_corrected_agreement": bc_point,
        "agreement_ci": [bc_lo, bc_hi],
        "structural_confidence": feats,
        "prior": prior,
        "judge_contributions": contrib,
        "canary_flags": canary_flags,
        "gate": {"ok": gate.ok(), "failures": gate.failures(),
                 "limitations": gate.limitations_line()},
        "gate_reason": reason,
        "ts": time.time(),
    }
    canon = json.dumps({k: verdict[k] for k in
                        ("question_id", "probability", "judge_contributions")},
                       sort_keys=True)
    verdict["verdict_sha256"] = hashlib.sha256(canon.encode()).hexdigest()[:16]
    return verdict


def record_verdict(verdict, path=VERDICT_LEDGER):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(verdict) + "\n")


def record_accepted_outcome(question_id, correct, path=None):
    """Append a resolved outcome for the abstention gate's history."""
    path = path or cal.HISTORY_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps({"question_id": question_id, "correct": bool(correct),
                            "ts": time.time()}) + "\n")
