#!/usr/bin/env python3
"""oracle-ask: the trivial ask path. One command consults the Oracle.

Usage:
  oracle-ask "Will X happen by <date>?" [--json] [--judges n] [--timeout s]
            [--evidence evidence.json] [--canaries] [--no-debate]

Pipeline: frame (fail-closed) -> judge panel in parallel (herd router) ->
calibrate -> pooled posterior (engine owns the number) -> abstention gate
-> escalation ladder -> verdict JSON on stdout + verdicts.jsonl.

Judge models: free-beats-local (SPEC §8.3). Defaults are the proven panel
from the 2026-09-20 herd census (see docs/oracle-core.md for why each won).
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
import sizing

HERD_URL = os.environ.get("HERD_URL", "http://127.0.0.1:25100")
WORK = os.environ.get("ORACLE_WORK", "/home/toxic/sovereign/agents/oracle-market/work")

# Proven panel defaults (docs/oracle-core.md §defaults).
DEFAULT_JUDGES = [
    "openrouter-free/nex-agi/nex-n2.5-mini:free",   # fastest exact: 489ms
    "openrouter-free/nex-agi/nex-n2.5-pro:free",    # exact 799ms, complement
    "openrouter-free/poolside/laguna-s-2.1:free",   # exact 2161ms, 3rd family
]
FALLBACK_JUDGE = "beellama/gemma-96k"               # local fallback only

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
        return {"ok": True, "text": text, "latency_s": time.time() - t0}
    except Exception as e:
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, e),
                "latency_s": time.time() - t0}


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
    jp.raw_response = res.get("text", "")[:2000]
    jp.latency_s = res.get("latency_s", 0)
    jp.error = res.get("error")
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
    """Full ask pipeline. Returns the verdict dict."""
    t0 = time.time()
    framed = framing.frame_question(question)
    if framed.get("status") == "refused":
        return engine.build_verdict(framed, [])
    models = models or list(DEFAULT_JUDGES)
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

    judges = []
    latencies = {}
    with cf.ThreadPoolExecutor(max_workers=len(models)) as ex:
        futs = {ex.submit(judge_once, m, prompt_for(i), timeout_s): (m, i)
                for i, m in enumerate(models)}
        deadline = t0 + budget_s
        for fut in cf.as_completed(futs, timeout=max(1, deadline - time.time())):
            m, i = futs[fut]
            try:
                jp = fut.result(timeout=max(1, deadline - time.time()))
            except Exception as e:
                jp = engine.JudgePosterior(judge_id=m, posterior=0.5, refused=True)
                jp.error = "executor: %s" % e
            ds = datasheets.get(m, {})
            jp.reliability = float(ds.get("reliability", 1.0))
            jp.cal_weight = 1.0  # calibration loop adjusts post-fit
            judges.append(jp)
            latencies[m] = getattr(jp, "latency_s", 0)
    judges.sort(key=lambda j: models.index(j.judge_id)
                if j.judge_id in models else 99)

    loop = cal.CalibrationLoop()
    for jp in judges:
        if not jp.refused:
            jp.posterior = loop.apply(jp.judge_id, jp.posterior)

    verdict = engine.build_verdict(framed, judges)
    verdict["latency_s"] = time.time() - t0
    verdict["judge_latencies"] = latencies
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
        debate = escalation.debate_tier(
            framed["binary_question"], framed["resolution_criteria"], ev_text,
            lambda prompt: extract_json(
                herd_chat(models[0 % len(models)], prompt, timeout_s).get("text", "")
                or "") or {"posterior": 0.5})
        # engine re-owns the debate output: deterministic mean of advocates
        verdict["probability"] = debate["posterior"]
        verdict["debate"] = {k: v for k, v in debate.items() if k != "trace"}
        verdict["debate_trace_n"] = len(debate["trace"])
        verdict["status"] = "verdict"
        verdict["tier"] = "DEBATE"
    elif tier == "HUMAN":
        path = escalation.flag_human(framed, tier_reason,
                                     {"verdict": verdict["probability"]})
        verdict["human_flag"] = path
    elif verdict["status"] == "escalate" and tier == "VOTE":
        # gate withheld but no disagreement: escalate path stays, engine honest
        verdict["tier"] = "VOTE"
    engine.record_verdict(verdict)
    return verdict


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
    ap.add_argument("--models", default=",".join(DEFAULT_JUDGES),
                    help="comma-separated herd model ids")
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
    return 0 if verdict.get("status") == "verdict" else 3


if __name__ == "__main__":
    sys.exit(main())
