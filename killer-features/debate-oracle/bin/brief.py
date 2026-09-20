#!/usr/bin/env python3
"""bin/brief.py -- build oracle.py's brief.json from debate-run output.

Input : runs/<debate_id>/transcript.json (bin/debate-run, t3-impl-orchestrator)
Output: brief.json per INTERFACE.md (what bin/oracle.py consumes).

Blinding: model names / lane identities are NOT carried into the brief
(anti self-preference). Candidate ORDER is preserved here; the runner
(bin/oracle.py) anonymizes to C1..Cn and shuffles. Abridging: per-turn
char caps (opening 2200, rebuttal 1800, close/final 1200).

Readiness: exits 0 READY (2-4 candidates, all rounds complete, >=1 live
lane per round), else 1 WAITING with reasons.

Usage: python3 bin/brief.py --run-dir runs/<debate_id> --brief-out <path>
"""
import argparse, json, os, sys

KIND_MAP = {"opening": "opening", "rebuttal": "rebuttal", "close": "final"}
CAP = {"opening": 2200, "rebuttal": 1800, "close": 1200}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--brief-out", required=True)
    a = ap.parse_args()

    with open(os.path.join(a.run_dir, "transcript.json")) as f:
        tr = json.load(f)
    cfg = tr["config"]
    task = tr["task"]
    lanes = cfg["lanes"]
    cand_by_id = {c["id"]: c for c in tr["candidates"]}
    undefended = set(tr.get("undefended", []))

    reasons = []
    if not (2 <= len(lanes) <= 4):
        reasons.append(f"candidates={len(lanes)} not in 2..4")
    if len(tr["rounds"]) != cfg["rounds"]:
        reasons.append(f"rounds {len(tr['rounds'])}/{cfg['rounds']} incomplete")
    for r in tr["rounds"]:
        if not any(t["status"] == "ok" for t in r["turns"].values()):
            reasons.append(f"round {r['n']}: no live lane")

    candidates = []
    for l in lanes:
        c = cand_by_id[l["candidate_id"]]
        candidates.append({
            "id": c["id"],
            "files": c.get("files"),
            "patch": c.get("patch"),
            "test_cmd": c.get("test_cmd", "pytest tests -q"),
            "claimed_strengths": c.get("claimed_strengths", []),
            "undefended": l["lane"] in undefended,
        })

    transcript = []
    for r in tr["rounds"]:
        for label, t in r["turns"].items():
            if t["status"] != "ok":
                continue
            lane = next(l for l in lanes if l["lane"] == label)
            transcript.append({
                "round": r["n"],
                "turn": label,
                "candidate_id": lane["candidate_id"],
                "kind": KIND_MAP.get(r["kind"], r["kind"]),
                "text": (t.get("argument") or "")[:CAP.get(r["kind"], 1500)],
            })

    brief = {
        "debate_id": tr["debate_id"],
        "task_ref": tr["task_id"],
        "spec": task["spec"],
        "hard_constraints": task.get("hard_constraints", []),
        "measured_failure": task.get("measured_failure"),
        "candidates": candidates,
        "transcript": transcript,
        "prompt_version": "oracle-v1",
    }
    if task.get("e2e_failure_notes"):
        brief["e2e_failure_notes"] = task["e2e_failure_notes"]

    with open(a.brief_out, "w") as f:
        json.dump(brief, f, indent=2)
    print(f"brief: {a.brief_out} "
          f"({len(candidates)} candidates, {len(transcript)} turns)")
    if reasons:
        print("readiness: WAITING (" + "; ".join(reasons) + ")")
        return 1
    print("readiness: READY")
    return 0


if __name__ == "__main__":
    sys.exit(main())
