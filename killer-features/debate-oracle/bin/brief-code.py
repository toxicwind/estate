#!/usr/bin/env python3
"""bin/brief-code.py -- render the blinded code-brief for oracle-judge --mode code.

Input : runs/<debate_id>/transcript.json (from bin/debate-run)
Output: brief markdown -- task spec + per-candidate {anonymized C1..Cn,
        patch/files, entry_cmd, test_cmd, claimed strengths, defended flag}
        + abridged transcript + e2e corpus pointer.

Blinding: candidate sources (kind/ref) stripped; order shuffled with a
recorded seed (default: sha256(debate_id)) -- anti self-preference/recency.
Prints readiness to stdout; exits 0 READY, 1 WAITING.
"""
import argparse, hashlib, json, os, random, sys

def render_candidate_code(cand, max_chars=6000):
    parts = []
    if cand.get("patch"):
        parts.append("```diff\n" + cand["patch"][:max_chars] + "\n```")
    for path, content in (cand.get("files") or {}).items():
        parts.append(f"### {path}\n```\n{(content or '')[:max_chars]}\n```")
    return "\n\n".join(parts) or "(no patch/files supplied)"

def render_brief_candidate(cand, defended, max_chars=3000):
    lines = []
    if cand.get("patch"):
        lines.append("```diff\n" + cand["patch"][:max_chars] + "\n```")
    for path, content in (cand.get("files") or {}).items():
        lines.append(f"### {path}\n```\n{(content or '')[:max_chars]}\n```")
    if cand.get("entry_cmd"):
        lines.append(f"entry_cmd: `{cand['entry_cmd']}`")
    if cand.get("test_cmd"):
        lines.append(f"test_cmd: `{cand['test_cmd']}`  <-- e2e gate runs this")
    if cand.get("claimed_strengths"):
        lines.append("claimed strengths: " + "; ".join(cand["claimed_strengths"]))
    lines.append(f"advocacy: {defended}")
    return "\n".join(lines) or "(no patch/files supplied)"


def abridge(transcript, label):
    """Per-candidate abridged transcript: opening + best rebuttal vs it + close."""
    out = []
    for r in transcript["rounds"]:
        t = r["turns"].get(label)
        if not t or t["status"] != "ok":
            out.append(f"#### Round {r['n']} ({r['kind']}): [{t['status'] if t else 'missing'}]")
            continue
        arg = t["argument"]
        if r["kind"] == "opening":
            out.append(f"#### Opening ({label})\n{arg[:2200]}")
        elif r["kind"] == "rebuttal":
            out.append(f"#### Rebuttal ({label})\n{arg[:1800]}")
        else:
            out.append(f"#### Close ({label})\n{arg[:1200]}")
    # strongest attack ON this candidate: vs-sections from others' rebuttals
    attacks = []
    for r in transcript["rounds"]:
        if r["kind"] != "rebuttal":
            continue
        for ol, t in r["turns"].items():
            if ol == label or t["status"] != "ok":
                continue
            for line in t["argument"].splitlines():
                if line.strip().lower().startswith(f"## vs {label}".lower()):
                    attacks.append(f"from {ol}: {line.strip()}")
    if attacks:
        out.append("#### Strongest attacks against %s\n%s" % (label, "\n".join(attacks[:4])))
    return "\n\n".join(out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--brief-out", required=True)
    ap.add_argument("--seed", default=None, help="shuffle seed (default: debate_id hash)")
    a = ap.parse_args()
    with open(os.path.join(a.run_dir, "transcript.json")) as f:
        tr = json.load(f)
    cfg = tr["config"]
    n_cand = len(cfg["lanes"])
    reasons = []
    if not (2 <= n_cand <= 4):
        reasons.append(f"candidates={n_cand} not in 2..4")
    if len(tr["rounds"]) != cfg["rounds"]:
        reasons.append(f"rounds {len(tr['rounds'])}/{cfg['rounds']} incomplete")
    for r in tr["rounds"]:
        if not any(t["status"] == "ok" for t in r["turns"].values()):
            reasons.append(f"round {r['n']}: no live lane")
    seed = a.seed or hashlib.sha256(tr["debate_id"].encode()).hexdigest()[:8]
    order = [l["lane"] for l in cfg["lanes"]]
    rnd = random.Random(seed)
    rnd.shuffle(order)
    anon = {label: f"C{i+1}" for i, label in enumerate(order)}  # brief label
    cand_by_label = {l["lane"]: next(c for c in tr["candidates"]
                                     if c["id"] == l["candidate_id"])
                       for l in cfg["lanes"]}
    lines = [f"# CODE BRIEF -- {tr['debate_id']}", "",
             f"task: {tr['task_id']} | rounds: {len(tr['rounds'])} | "
             f"shuffle_seed: {seed} (order blinded, reproducible)", "",
             "## Task spec", tr["task"]["spec"], "",
             "## Hard constraints"]
    lines += [f"- {c}" for c in tr["task"]["hard_constraints"]]
    if tr["task"].get("measured_failure"):
        lines += ["", "## Measured failure mode", tr["task"]["measured_failure"]]
    if tr["task"].get("e2e_failure_notes"):
        lines += ["", "## Re-debate constraints (e2e failures)", tr["task"]["e2e_failure_notes"]]
    lines += ["", "## Candidates (anonymized, order shuffled)"]
    for label in order:
        lane = next(l for l in cfg["lanes"] if l["lane"] == label)
        defended = ("DEFENDED" if label not in tr.get("undefended", [])
                    else "UNDEFENDED (champion cut every round)")
        lines += ["", f"### {anon[label]} [{defended}]",
                  f"debate-label: {label} | model: {lane['model']}",
                  render_brief_candidate(cand_by_label[label], defended)]
    lines += ["", "## Abridged transcript"]
    for label in order:
        lines += ["", f"### {anon[label]}", abridge(tr, label)]
    lines += ["", "## E2E corpus pointer",
              "Run each candidate's test_cmd from its candidate.json in the t3-e2e sandbox.",
              f"Run dir: {os.path.abspath(a.run_dir)}"]
    with open(a.brief_out, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"brief: {a.brief_out}")
    if reasons:
        print("readiness: WAITING (" + "; ".join(reasons) + ")")
        return 1
    print("readiness: READY (candidates 2..4, all rounds complete, >=1 live lane/round)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
