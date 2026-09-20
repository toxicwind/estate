#!/usr/bin/env python3
"""oracle-ask: the ask path. One command consults the Oracle.

Usage:
  oracle-ask "Will X happen by <date>?" [--json] [--models a,b,c] [--timeout s]
            [--evidence evidence.json] [--canaries] [--no-debate]

Pipeline: frame (fail-closed) -> resilient judge panel in parallel (herd
router) -> pooled posterior (engine owns the number: calibration +
aggregation + gate, exactly once) -> escalation ladder -> verdict JSON on
stdout + verdicts.jsonl.

ROUTER SEPARATION (standing doctrine): this file names only judge ROLE
ALIASES (oracle-judge-a/b/c, oracle-judge-local). Concrete model selection
lives in the herd router config (config/herd.yaml, "Oracle judge panel")
and is owned there exclusively. --models accepts aliases only; concrete
model IDs are rejected. To retarget the panel, edit herd.yaml and restart
herd -- never this file.

Judge models: free-beats-local (SPEC §8.3). The panel shape (3 free-tier
aliases + local fallback) is the proven default from the 2026-09-20 herd
census (see docs/oracle-core.md for the rationale).
"""
import argparse
import concurrent.futures as cf
import json
import os
import sys
import time
import urllib.request

BIN = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BIN)

import framing
import calibration as cal
import engine
import evidence as evmod
import escalation

HERD_URL = os.environ.get("HERD_URL", "http://127.0.0.1:25100")
WORK = os.environ.get("ORACLE_WORK", "/home/toxic/sovereign/agents/oracle-market/work")

# Judge panel: ROUTER ROLE ALIASES. Concrete targets are owned by
# config/herd.yaml ("Oracle judge panel"); this list is routing surface
# only, never model-family selection.
DEFAULT_JUDGES = [
    "oracle-judge-a",
    "oracle-judge-b",
    "oracle-judge-c",
]
FALLBACK_JUDGE = "oracle-judge-local"  # local last resort, router-owned

JUDGE_PROMPT = """You are judge {idx} (anonymous) on the OpenFang Oracle panel.
Question: {question}
Resolution criteria: {criteria}
Base-rate prior: {prior:.2f} (start here; move only on evidence).

First argue BOTH sides to yourself in one line each, then judge.
OVERCONFIDENCE ADVISORY: judges are systematically overconfident. Report a
posterior above 0.90 or below 0.10 only if you would stake your own money on it.

Reply with JSON ONLY, no other text:
{{"posterior": <0..1, probability the answer is YES>,
  "verbal_confidence": "<low|medium|high>",
  "claims": [{{"text": "<one atomic factual claim>",
               "stance": "<supports_yes|supports_no|neutral>",
               "llr": <signed strength in nats, |llr|<=2.0>,
               "cluster_id": "<shared id when the same underlying fact>",
               "rationale": "<one line>", "urls": [],
               "credibility": "<low|medium|high>"}}],
  "reasoning_summary": "<2-3 sentences>"}}"""


def _env_models():
    raw = os.environ.get("ORACLE_JUDGES", ",".join(DEFAULT_JUDGES))
    return [m.strip() for m in raw.split(",") if m.strip()]


def _alias_allowlist():
    extra = [m.strip() for m in os.environ.get("ORACLE_JUDGES", "").split(",")
             if m.strip()]
    return set(DEFAULT_JUDGES + [FALLBACK_JUDGE] + extra)


def _check_alias_models(models):
    """Fail closed: only router aliases may serve as judges. Concrete
    model IDs (with /, :, or known family names) are never accepted --
    model selection lives in herd.yaml, not here."""
    bad = [m for m in models if m not in _alias_allowlist()]
    if bad:
        raise SystemExit(
            "refusing non-alias judge model(s): %s. Model selection lives "
            "in the herd router config (config/herd.yaml); add panel "
            "aliases via ORACLE_JUDGES." % ", ".join(bad))


def herd_chat(model, prompt, timeout_s=90, max_tokens=1500):
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }).encode()
    req = urllib.request.Request(
        HERD_URL + "/v1/chat/completions", data=body,
        headers={"Content-Type": "application/json"}, method="POST")
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as r:
            data = json.load(r)
        text = data["choices"][0]["message"]["content"]
        return {"ok": True, "text": text, "latency_s": time.time() - t0,
                "usage": data.get("usage") or {}}
    except Exception as e:
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, e),
                "latency_s": time.time() - t0, "usage": {}}


def extract_json(text):
    """Robust JSON extraction: first balanced {...} block."""
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    instr = esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if instr:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                instr = False
        else:
            if ch == '"':
                instr = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except Exception:
                        return None
    return None


def judge_once(model, prompt, timeout_s):
    """One judge call -> engine.JudgePosterior. Unparseable/refused judges
    are marked refused and contribute nothing (never fabricated)."""
    res = herd_chat(model, prompt, timeout_s)
    jp = engine.JudgePosterior(judge_id=model, posterior=0.5, refused=True)
    jp.raw_response = (res.get("text") or "")[:2000]
    jp.latency_s = res.get("latency_s", 0)
    jp.error = res.get("error")
    jp.usage = res.get("usage") or {}
    if not res["ok"]:
        return jp
    data = extract_json(res["text"] or "")
    if not isinstance(data, dict):
        return jp
    try:
        p = float(data.get("posterior", 0.5))
    except (TypeError, ValueError):
        return jp
    claims = []
    for c in data.get("claims") or []:
        if isinstance(c, dict) and c.get("text"):
            claims.append(c)
    jp.refused = False
    jp.posterior = min(0.999, max(0.001, p))
    jp.verbal_conf = data.get("verbal_confidence")
    jp.claims = claims
    return jp


def _resilient_judge(model, prompt, timeout_s, judge_fn=judge_once):
    """One panel slot with fail-fast redundancy.

    Try the slot alias; on refusal, one bounded retry at half timeout
    (free-tier flakiness is transient); if still refused, the
    local-fallback alias fills the slot. Returns (JudgePosterior,
    slot_info). A refused slot never silently shrinks the panel -- the
    slot_info records who actually served it.
    """
    attempts = 0
    jp = judge_fn(model, prompt, timeout_s); attempts += 1
    if jp.refused:
        jp = judge_fn(model, prompt, min(timeout_s, 45.0) / 2.0); attempts += 1
    served_by = model
    if jp.refused and model != FALLBACK_JUDGE:
        fb = judge_fn(FALLBACK_JUDGE, prompt, 60.0); attempts += 1
        if not fb.refused:
            fb.judge_id = FALLBACK_JUDGE
            jp = fb
            served_by = FALLBACK_JUDGE
    return jp, {"slot": model, "served_by": served_by,
                "refused": jp.refused, "attempts": attempts}


def load_datasheets():
    if os.path.exists(cal.DATASHEET_PATH):
        try:
            with open(cal.DATASHEET_PATH) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def run_ask(question, models=None, timeout_s=90, evidence_items=None,
            allow_debate=True, budget_s=240):
    """Full ask pipeline. Returns the verdict dict.

    Calibration ownership: engine.build_verdict is the SOLE applier of
    calibration. This function never touches judge posteriors between
    receipt and the engine (double application was removed 2026-09-20).
    """
    t0 = time.time()
    t_f0 = time.time()
    framed = framing.frame_question(question)
    t_frame = time.time() - t_f0
    if framed.get("status") == "refused":
        return engine.build_verdict(framed, [])
    models = models or _env_models()
    _check_alias_models(models)
    datasheets = load_datasheets()

    # evidence partitions (asymmetry) — empty for pure-judgment asks
    partition = None
    if evidence_items:
        partition = evmod.partition_evidence(evidence_items, len(models))

    def prompt_for(i):
        base = JUDGE_PROMPT.format(
            idx=i + 1, question=framed["binary_question"],
            criteria=framed["resolution_criteria"],
            prior=framed["base_rate_prior"])
        if partition:
            base += ("\n\nEVIDENCE VIEW:\n" +
                     evmod.summarize_evidence_for_judge(partition, i))
        return base

    calls = 0
    judges = []
    latencies = {}
    slots = []
    usages = []
    t_j0 = time.time()
    with cf.ThreadPoolExecutor(max_workers=len(models)) as ex:
        futs = {ex.submit(_resilient_judge, m, prompt_for(i), timeout_s): (m, i)
                for i, m in enumerate(models)}
        deadline = t0 + budget_s
        for fut in cf.as_completed(futs):  # no outer timeout: its TimeoutError
            # escaped uncaught with pending futures. Every slot is
            # time-bounded by construction and each fut.result() below
            # is deadline-bounded, so this loop always terminates.
            m, i = futs[fut]
            try:
                jp, slot = fut.result(timeout=max(1, deadline - time.time()))
            except Exception as e:
                jp = engine.JudgePosterior(judge_id=m, posterior=0.5,
                                           refused=True)
                jp.error = "executor: %s" % e
                slot = {"slot": m, "served_by": m, "refused": True}
            calls += slot.get("attempts", 1)  # actual requests, incl. bounded retries
            ds = datasheets.get(jp.judge_id, datasheets.get(m, {}))
            jp.reliability = float(ds.get("reliability", 1.0))
            jp.cal_weight = 1.0
            judges.append(jp)
            slots.append(slot)
            latencies[m] = getattr(jp, "latency_s", 0)
            usages.append(getattr(jp, "usage", None) or {})
    t_judge = time.time() - t_j0
    judges.sort(key=lambda j: models.index(j.judge_id)
                if j.judge_id in models else 99)

    # NOTE: no calibration here. engine.build_verdict applies the
    # calibration loop exactly once, deterministically, then aggregates.
    t_e0 = time.time()
    verdict = engine.build_verdict(framed, judges)
    t_engine = time.time() - t_e0
    verdict["timing"] = {"frame_s": round(t_frame, 3),
                         "judge_s": round(t_judge, 3),
                         "engine_s": round(t_engine, 3)}
    verdict["latency_s"] = time.time() - t0
    verdict["judge_latencies"] = latencies
    verdict["judge_slots"] = slots
    verdict["models"] = models

    # escalation ladder: route on the ABSTENTION decision (the emission gate),
    # not the full RefusalGate ledger (which stays strict/honest by design:
    # NOT_CHECKED never passes silently, but it routes via limitations).
    gate_ok = (verdict["status"] == "verdict")
    live_posts = [j.posterior for j in judges if not j.refused]
    tier, tier_reason = escalation.route(
        live_posts, verdict["structural_confidence"]["confidence"], gate_ok)
    verdict["tier"] = tier
    verdict["tier_reason"] = tier_reason
    if tier == "DEBATE" and allow_debate:
        ev_text = "\n".join(
            "- " + (c.get("text", "") or "") for j in judges for c in j.claims[:4])

        debate_usages = []

        def _debate_chat(model, prompt, t):
            res = herd_chat(model, prompt, t, max_tokens=400)
            debate_usages.append(res.get("usage") or {})
            return {"content": res.get("text") or ""}

        budget_left = max(10.0, budget_s - (time.time() - t0))
        t_d0 = time.time()
        debate = escalation.debate_tier(
            framed["binary_question"], framed["resolution_criteria"], ev_text,
            judges=models,  # router aliases; distinct per advocate
            chat_fn=_debate_chat,
            k=escalation.DEBATE_K, max_rounds=escalation.DEBATE_MAX_ROUNDS,
            eps=escalation.DEBATE_EPS,
            per_advocate_timeout_s=min(90.0, budget_left / 2.0))
        calls += debate.get("requests",
                        debate["rounds"] * len(debate["advocate_finals"]))
        # Engine re-owns the debate output: advocate finals become
        # half-weight judges (they share one converged trajectory, so
        # k advocates/side ~= 1 independent judge/side of evidence).
        # Gates, confidence, contributions, and the verdict hash are all
        # recomputed on the final number -- the vote verdict is kept only
        # for provenance. Nothing is overwritten in place.
        adv_judges = [
            engine.JudgePosterior(judge_id=a["model"],
                                  posterior=a["posterior"], cal_weight=0.5)
            for a in debate["advocate_finals"]]
        final = engine.build_verdict(framed, adv_judges)
        final["tier"] = "DEBATE"
        final["tier_reason"] = (
            "structured advocate debate: %d rounds%s"
            % (debate["rounds"],
               ", converged" if debate["converged"] else ", budget-capped"))
        final["debate"] = {
            "rounds": debate["rounds"],
            "converged": debate["converged"],
            "internal_posterior": debate["posterior"],
            "advocate_finals": debate["advocate_finals"],
            "vote_probability": verdict["probability"],
            "vote_status": verdict["status"],
            "vote_tier": verdict["tier"],
        }
        final["vote_verdict"] = verdict  # provenance, not the decision
        final["judge_slots"] = slots
        final["judge_latencies"] = latencies
        final["models"] = models
        final["latency_s"] = time.time() - t0
        final["timing"] = dict(verdict.get("timing") or {},
                               debate_s=round(time.time() - t_d0, 3))
        final["cost_usd"] = round(calls * 0.002, 6)
        final["llm_calls"] = calls
        final["usage_cost_usd"] = round(
            sum(_usage_cost(u) for u in usages + debate_usages), 6)
        engine.record_verdict(final)
        return final
    elif tier == "HUMAN":
        path = escalation.flag_human(framed, tier_reason,
                                     {"verdict": verdict["probability"]})
        verdict["human_flag"] = path
    elif verdict["status"] == "escalate" and tier == "VOTE":
        # gate withheld but no disagreement: escalate path stays, engine honest
        verdict["tier"] = "VOTE"
    verdict["cost_usd"] = round(calls * 0.002, 6)
    verdict["llm_calls"] = calls
    verdict["usage_cost_usd"] = round(sum(_usage_cost(u) for u in usages), 6)
    engine.record_verdict(verdict)
    return verdict


def _usage_cost(u):
    """Measured upstream cost of one herd call from its usage block.
    Free-tier judges report cost 0; missing usage -> 0.0 (honest, not
    imputed). Kept separate from cost_usd, which is the code's flat
    per-request accounting estimate."""
    if not isinstance(u, dict):
        return 0.0
    c = u.get("cost")
    try:
        return float(c) if c else 0.0
    except (TypeError, ValueError):
        return 0.0


def run_canaries(models=None, timeout_s=90):
    """Ask every seeded canary; returns per-judge gaming report."""
    import glob
    reports = []
    for path in sorted(glob.glob(os.path.join(BIN, "..", "bench",
                                              "canary_*.json"))):
        with open(path) as f:
            spec = json.load(f)
        v = run_ask(spec["question"], models=models, timeout_s=timeout_s,
                    allow_debate=False)
        reports.append({"canary": os.path.basename(path),
                        "answer": spec["answer"],
                        "verdict_p": v.get("probability"),
                        "correct": ((v.get("probability", 0.5) >= 0.5)
                                    == bool(spec["answer"]))
                        if v.get("status") == "verdict" else None,
                        "status": v.get("status")})
    return reports


def main(argv=None):
    ap = argparse.ArgumentParser(description="Ask the OpenFang Oracle.")
    ap.add_argument("question", nargs="?", default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--models", default=",".join(_env_models()),
                    help="comma-separated herd judge aliases "
                         "(router role aliases only; concrete model IDs "
                         "are refused)")
    ap.add_argument("--timeout", type=float, default=90)
    ap.add_argument("--budget", type=float, default=240)
    ap.add_argument("--evidence", default=None, help="JSON file of evidence items")
    ap.add_argument("--canaries", action="store_true")
    ap.add_argument("--no-debate", action="store_true")
    args = ap.parse_args(argv)

    if args.canaries:
        rep = run_canaries(models=args.models.split(","), timeout_s=args.timeout)
        print(json.dumps(rep, indent=2))
        return 0
    if not args.question:
        ap.error("a question is required (or --canaries)")
    items = None
    if args.evidence:
        with open(args.evidence) as f:
            items = json.load(f)
    verdict = run_ask(args.question, models=args.models.split(","),
                      timeout_s=args.timeout, evidence_items=items,
                      allow_debate=not args.no_debate, budget_s=args.budget)
    if args.json or True:
        print(json.dumps(verdict, indent=2, default=str))
    return 0 if verdict.get("status") in ("verdict", "escalate") else 3


if __name__ == "__main__":
    sys.exit(main())
