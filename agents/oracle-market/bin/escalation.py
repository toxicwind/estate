#!/usr/bin/env python3
"""Escalation ladder — the routing doctrine (arXiv:2605.30802).

Default path: parallel independent judgments + pooled-posterior vote.
Debate is an ESCALATION TIER, triggered by disagreement or low margin —
never the default (debate alone is a martingale over belief trajectories,
arXiv:2508.17536; deliberative consensus degraded accuracy to ~76%,
arXiv:2605.30802).

Tiers:
  AUTO    unanimous + high-confidence posteriors -> auto-resolve
          (97.87% precedent on 47% of volume)
  VOTE    pooled posterior verdict, gate passed -> emit
  DEBATE  disagreement / low margin / invariant violation ->
          structured debate, D3 MORE-style: k parallel anonymized advocates
          per side, budgeted stopping, convergence checks, correction-biased
          updates (arXiv:2410.04663; debate-or-vote alpha intervention)
  HUMAN   persistent disagreement -> human arbitration flag (file + fleet note)

Every routing decision records its rationale. Debate is a cost center.
"""
import json
import os
import time

WORK = os.environ.get("ORACLE_WORK", "/home/toxic/sovereign/agents/oracle-market/work")
ESCALATION_DIR = os.path.join(WORK, "escalations")

# Defaults (proven values documented in docs/oracle-core.md).
AUTO_BAR = 0.85          # unanimity posterior bar per side
DEBATE_K = 2             # parallel advocates per side (D3 MORE)
DEBATE_MAX_ROUNDS = 3    # budgeted stopping: hard cap
DEBATE_EPS = 0.03        # convergence: stop if max |Δposterior| < eps
DISAGREE_MARGIN = 0.25   # spread above this triggers DEBATE


def route(judge_posteriors, struct_confidence, gate_ok, invariant_ok=True):
    """Decide the tier. judge_posteriors: list of floats (live judges only)."""
    posts = [p for p in judge_posteriors]
    if not posts:
        return ("HUMAN", "no live judges — nothing to aggregate")
    if not invariant_ok:
        return ("DEBATE", "probability-axiom invariant violation")
    if not gate_ok:
        return ("DEBATE", "abstention gate withheld the verdict")
    unanimous_yes = all(p >= AUTO_BAR for p in posts)
    unanimous_no = all(p <= 1 - AUTO_BAR for p in posts)
    if (unanimous_yes or unanimous_no) and struct_confidence >= 0.90:
        return ("AUTO", "unanimous high-confidence (%d judges)" % len(posts))
    spread = max(posts) - min(posts)
    yes = sum(1 for p in posts if p >= 0.5)
    if spread >= DISAGREE_MARGIN or (0 < yes < len(posts) and struct_confidence < 0.6):
        return ("DEBATE", "disagreement: spread=%.2f, %d/%d yes" %
                (spread, yes, len(posts)))
    return ("VOTE", "pooled posterior path, spread=%.2f" % spread)


ADVOCATE_PROMPT = """You are an anonymous advocate in a structured debate.
Question: {question}
Resolution criteria: {criteria}
You argue the {side} side. Other advocates (anonymous, like you) argue both sides.
Shared evidence:
{evidence}
Round {round_no}/{max_rounds}. Prior pooled probability: {prior:.2f}.
Update TOWARD CORRECTION, not toward defending your side: if the evidence
against your side is stronger, say so and move your number accordingly.
Reply as JSON only: {{"posterior": <0..1>, "strongest_claim": "<one sentence>",
"concession": "<strongest point against your side, or null>"}}"""


def debate_tier(question, criteria, evidence_text, judge_fn,
                k=DEBATE_K, max_rounds=DEBATE_MAX_ROUNDS, eps=DEBATE_EPS):
    """D3 MORE-style debate: k parallel anonymized advocates per side,
    budgeted stopping, convergence checks, correction-biased updates.

    judge_fn(prompt) -> {"posterior": float, ...}. Advocates are anonymous
    (no model names in prompts) and role-diversified; both sides see the
    same shared evidence (asymmetry lives in the vote tier, not here).
    Returns {"posterior", "rounds", "converged", "trace"}.
    """
    sides = ["YES", "NO"]
    advocates = [{"side": s, "idx": i, "posterior": 0.5 if s == "YES" else 0.5}
                 for s in sides for i in range(k)]
    trace = []
    prior = 0.5
    converged = False
    rounds_run = 0
    for rnd in range(1, max_rounds + 1):
        rounds_run = rnd
        max_delta = 0.0
        for adv in advocates:
            prompt = ADVOCATE_PROMPT.format(
                question=question, criteria=criteria, side=adv["side"],
                evidence=evidence_text, round_no=rnd, max_rounds=max_rounds,
                prior=prior)
            try:
                out = judge_fn(prompt) or {}
                new_p = float(out.get("posterior", adv["posterior"]))
            except Exception:
                new_p = adv["posterior"]
            new_p = min(0.99, max(0.01, new_p))
            max_delta = max(max_delta, abs(new_p - adv["posterior"]))
            adv["posterior"] = new_p
            trace.append({"round": rnd, "side": adv["side"], "idx": adv["idx"],
                          "posterior": new_p,
                          "concession": (out.get("concession")
                                         if isinstance(out, dict) else None)})
        # pooled posterior of advocates = simple mean here (engine re-weighs later)
        prior = sum(a["posterior"] for a in advocates) / len(advocates)
        if max_delta < eps:
            converged = True
            break
    return {"posterior": prior, "rounds": rounds_run, "converged": converged,
            "trace": trace,
            "note": "budgeted stop at %d/%d rounds" % (rounds_run, max_rounds)}


def flag_human(question_record, reason, context=None):
    """Human arbitration flag: durable file + return the path. The caller
    (oracle_ask / daemon) posts the fleet note — this function never sends."""
    os.makedirs(ESCALATION_DIR, exist_ok=True)
    flag = {
        "ts": time.time(),
        "question_id": question_record.get("question_id"),
        "question": question_record.get("binary_question"),
        "reason": reason,
        "context": context or {},
        "status": "awaiting_human",
    }
    path = os.path.join(ESCALATION_DIR,
                        "human-%s.json" % flag["question_id"])
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(flag, f, indent=2)
    os.replace(tmp, path)
    return path


def resolve_human_flag(question_id, resolution, rationale=""):
    path = os.path.join(ESCALATION_DIR, "human-%s.json" % question_id)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        flag = json.load(f)
    flag["status"] = "resolved"
    flag["resolution"] = resolution
    flag["rationale"] = rationale
    flag["resolved_ts"] = time.time()
    with open(path, "w") as f:
        json.dump(flag, f, indent=2)
    return flag
