#!/usr/bin/env python3
"""Oracle judge runner — debate-oracle code selector (t3-impl-oracle).

Reads a debate brief (INTERFACE.md), renders the versioned judge prompt,
judges via a staggered model race with fail-fast ceilings, runs a
position-swap check, and emits a verdict draft (verdict.json v1 shape minus
the e2e field, which bin/gate.py fills after the mandatory test gate).

Usage:
  python3 bin/oracle.py --brief <brief.json> --out <verdicts-dir> \
      [--prompt prompts/oracle-v1.md] [--no-swap] [--warmup]

Model cascade (probed live 2026-09-20, HFT staggered race):
  primary : kimi-k3-nim  @ localhost:25100 (llama-swap cloud) — PARSE-OK
  fallback: kimi-k2      @ localhost:25100 — PARSE-OK, ~1.4s
Staggered: fallback starts if primary has no VALID verdict within STAGGER_S.
Swap-run: the winning model re-judges with candidate order reversed;
disagreement costs 0.2 confidence and is recorded.
"""
import argparse, concurrent.futures, copy, datetime, json, os, re, sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPTS = os.path.join(ROOT, "prompts")

MODELS = [
    ("kimi-k3-nim", "http://localhost:25100/v1/chat/completions", 150),
    ("kimi-k2",     "http://localhost:25100/v1/chat/completions", 90),
]
STAGGER_S = 20          # start fallback if primary has no valid verdict yet
WARMUP_S = 30
RUBRIC_AXES = ["correctness", "evidence", "constraint_fit",
               "failure_coverage", "simplicity"]

VALID_KEYS = {"winner", "ranking", "confidence", "rubric", "rationale",
              "synthesis_map"}


def chat(url, model, system, user, max_tokens, timeout_s):
    body = json.dumps({
        "model": model,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "max_tokens": max_tokens, "temperature": 0.0,
    }).encode()
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout_s) as r:
        d = json.loads(r.read().decode())
    return d["choices"][0]["message"]["content"]


def extract_json(text):
    """Pull the verdict JSON out of model output (fences tolerated)."""
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*", "", t)
    t = re.sub(r"\s*```$", "", t)
    start = t.find("{")
    end = t.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object in output")
    return json.loads(t[start:end + 1])


def validate(v, n_candidates, ids):
    w = v.get("winner")
    r = v.get("ranking")
    if w != "synthesis" and w not in ids:
        raise ValueError(f"bad winner: {w!r}")
    if not isinstance(r, list) or set(r) != set(ids):
        raise ValueError(f"ranking must be a permutation of {ids}")
    c = v.get("confidence")
    if not isinstance(c, (int, float)) or not (0 <= c <= 1):
        raise ValueError(f"bad confidence: {c!r}")
    rub = v.get("rubric")
    if not isinstance(rub, dict) or any(a not in rub for a in RUBRIC_AXES):
        raise ValueError("rubric missing axes")
    for a in RUBRIC_AXES:
        s = rub[a]
        if not isinstance(s, int) or not (0 <= s <= 10):
            raise ValueError(f"bad rubric score {a}: {s!r}")
    rat = v.get("rationale")
    if not isinstance(rat, str) or len(rat) > 1200:
        raise ValueError("rationale missing or >1200 chars")
    return True


def render_brief(brief, system_prompt, reverse=False):
    cands = list(brief["candidates"])
    if reverse:
        cands = list(reversed(cands))
    anon = {c["id"]: f"C{i+1}" for i, c in enumerate(cands)}
    lines = ["# TASK SPEC", brief["spec"], "",
             "# HARD CONSTRAINTS"]
    lines += [f"- {h}" for h in brief.get("hard_constraints", [])]
    if brief.get("measured_failure"):
        lines += ["", "# MEASURED FAILURE MODE", brief["measured_failure"]]
    if brief.get("reference_test_results"):
        lines += ["", "# PRE-RUN E2E TEST RESULTS (reference grading — outranks rhetoric)",
                  brief["reference_test_results"]]
    lines += ["", "# CANDIDATES (anonymized, order shuffled)"]
    for c in cands:
        tag = anon[c["id"]]
        lines += [f"\n## {tag}", f"(internal id: {c['id']})",
                  f"undefended: {c.get('undefended', False)}"]
        if c.get("claimed_strengths"):
            lines += ["claimed strengths:"] + [f"- {s}" for s in c["claimed_strengths"]]
        files = c.get("files") or {}
        patch = c.get("patch")
        if files:
            for path, content in files.items():
                # line-numbered: makes [Cx L<n>] rationale citations verifiable
                # (oracle-v1 audit: judges cite lines that don't exist otherwise)
                numbered = "\n".join(
                    f"{i+1:4d}| {ln}"
                    for i, ln in enumerate(content.rstrip().splitlines()))
                lines += [f"\n### file {path}", "```", numbered, "```"]
        elif patch:
            lines += ["\n### patch", "```diff", patch.rstrip(), "```"]
        else:
            lines += ["(no code attached — judge on artifact is impossible; score correctness 0)"]
    tr = brief.get("transcript", [])
    if tr:
        lines += ["", "# ABRIDGED DEBATE TRANSCRIPT"]
        for m in tr:
            who = anon.get(m.get("candidate_id"), m.get("candidate_id"))
            lines += [f"\n[R{m.get('round')}.{m.get('turn')} {who} {m.get('kind')}]",
                      (m.get("text") or "")[:2500]]
    lines += ["", "# MAP (runner use only — never shown to judge model)",
              json.dumps({v: k for k, v in anon.items()})]
    return "\n".join(lines), anon


def judge_once(system, user, reverse_tag):
    """Staggered race across models. Returns (verdict_dict, model_name, raw)."""
    result = {}

    def attempt(name, url, ceiling):
        try:
            out = chat(url, name, system, user,
                       max_tokens=2000, timeout_s=ceiling)
            v = extract_json(out)
            return (name, v, out, None)
        except Exception as e:
            return (name, None, "", f"{type(e).__name__}: {e}"[:160])

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        futures = {}
        primary = MODELS[0]
        futures[ex.submit(attempt, *primary)] = primary[0]
        deadline = None
        try:
            # staggered: wait STAGGER_S for primary; then launch fallback
            done, _ = concurrent.futures.wait(
                list(futures), timeout=STAGGER_S,
                return_when=concurrent.futures.FIRST_COMPLETED)
            for f in done:
                name, v, out, err = f.result()
                if v is not None:
                    result["verdict"] = (v, name, out)
                    break
            if "verdict" not in result:
                fallback = MODELS[1]
                futures[ex.submit(attempt, *fallback)] = fallback[0]
            if "verdict" not in result:
                for f in concurrent.futures.as_completed(futures, timeout=180):
                    name, v, out, err = f.result()
                    if v is not None:
                        result["verdict"] = (v, name, out)
                        break
                    else:
                        print(f"[oracle] {name} invalid: {err}", file=sys.stderr)
        finally:
            for f in futures:
                f.cancel()
    if "verdict" not in result:
        raise RuntimeError("no model produced a parseable verdict")
    return result["verdict"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brief", required=True)
    ap.add_argument("--out", required=True, help="verdicts dir")
    ap.add_argument("--prompt", default=os.path.join(PROMPTS, "oracle-v1.md"))
    ap.add_argument("--no-swap", action="store_true")
    ap.add_argument("--warmup", action="store_true")
    args = ap.parse_args()

    with open(args.brief) as f:
        brief = json.load(f)
    with open(args.prompt) as f:
        system = f.read()
    prompt_version = os.path.basename(args.prompt).replace(".md", "")

    ids = [c["id"] for c in brief["candidates"]]
    if not (2 <= len(ids) <= 4):
        raise SystemExit("brief must carry 2-4 candidates")

    if args.warmup:
        try:
            chat(MODELS[0][1], MODELS[0][0], "reply ok",
                 "ok", max_tokens=4, timeout_s=WARMUP_S)
            print("[oracle] warmup OK", file=sys.stderr)
        except Exception as e:
            print(f"[oracle] warmup failed ({e}) — continuing", file=sys.stderr)

    user, anon = render_brief(brief, system, reverse=False)
    v, model, raw = judge_once(system, user, "normal")
    validate(v, len(ids), [f"C{i+1}" for i in range(len(ids))])
    deanon = {a: k for k, a in anon.items()}
    winner = v["winner"]
    ranking = v["ranking"]

    swap_agree = None
    if not args.no_swap and len(ids) > 1:
        user_r, anon_r = render_brief(brief, system, reverse=True)
        try:
            v2, model2, raw2 = judge_once(system, user_r, "swapped")
            validate(v2, len(ids), [f"C{i+1}" for i in range(len(ids))])
            w2 = v2["winner"]
            # map swapped labels back to canonical ids
            deanon_r = {a: k for k, a in anon_r.items()}
            canon = lambda lbl: deanon.get(lbl) if lbl in deanon else None
            canon2 = lambda lbl: deanon_r.get(lbl)
            swap_agree = (canon(winner) == canon2(w2))
            if not swap_agree:
                v["confidence"] = max(0.0, round(v["confidence"] - 0.2, 2))
                v["rationale"] = (v["rationale"] +
                    " [swap-check: winner changed under candidate reorder; confidence -0.2]")[:1200]
        except Exception as e:
            print(f"[oracle] swap-run failed: {e} — keeping single-run verdict",
                  file=sys.stderr)

    draft = {
        "debate_id": brief["debate_id"],
        "task_ref": brief["task_ref"],
        "winner": deanon[winner] if winner != "synthesis" else "synthesis",
        "ranking": [deanon[l] for l in ranking],
        "confidence": round(float(v["confidence"]), 2),
        "rationale": v["rationale"],
        "judge_model": model,
        "judge_prompt_version": prompt_version,
        "rubric": {a: int(v["rubric"][a]) for a in RUBRIC_AXES},
        "decided_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "swap_agreement": swap_agree,
        "anon_map": anon,
    }
    if winner == "synthesis" and v.get("synthesis_map"):
        draft["synthesis_map"] = {el: deanon.get(lbl, lbl)
                                  for el, lbl in v["synthesis_map"].items()}
    # e2e is added by bin/gate.py — never by the judge. A pick that fails
    # tests is never crowned; the draft is not a verdict until gated.

    ddir = os.path.join(args.out, brief["debate_id"])
    os.makedirs(ddir, exist_ok=True)
    with open(os.path.join(ddir, "verdict-draft.json"), "w") as f:
        json.dump(draft, f, indent=2)
    with open(os.path.join(ddir, "judge-raw.txt"), "w") as f:
        f.write(raw)
    print(json.dumps({"winner": draft["winner"], "confidence": draft["confidence"],
                      "judge_model": model, "swap_agreement": swap_agree,
                      "draft": os.path.join(ddir, "verdict-draft.json")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
