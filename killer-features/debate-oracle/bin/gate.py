#!/usr/bin/env python3
"""E2E gate finalizer — debate-oracle oracle side (t3-impl-oracle).

MANDATORY: the oracle's winner MUST pass the task's real acceptance tests
before being crowned. A judge pick that fails tests is NEVER the answer.

Ownership: test EXECUTION is t3-e2e's (e2e/gate.py — verdict + candidates ->
walk winner+ranking, run pytest in the e2e venv, verdict.gated.json).
This script is the oracle-side finalizer on top of it:

  1. materializes candidates from the brief into a candidates dir
  2. runs e2e/gate.py (subprocess, fail-fast — no polling)
  3. on all-fail: emits redebate.json with e2e_failure_notes (failure logs
     as new constraints; architect's fallback: ONE re-debate allowed, then
     fail-to-fleet — the re-debate trigger is the orchestrator's job)
  4. normalizes e2e.status to the schemas/verdict.json v1 enum
     (t3-e2e's "fail" -> schema "failed")
  5. writes the canonical final verdicts/<debate_id>/verdict.json
  6. appends the verdict ledger verdicts/VERDICTS.jsonl

Usage:
  python3 bin/gate.py --debate <debate_id> --brief <brief.json> \
      --verdicts <verdicts-dir> --tasks-root <tasks/> [--timeout 120]
"""
import argparse, datetime, json, os, shutil, subprocess, sys

E2E_GATE = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "e2e", "gate.py")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--debate", required=True)
    ap.add_argument("--brief", required=True)
    ap.add_argument("--verdicts", required=True)
    ap.add_argument("--tasks-root", required=True)
    ap.add_argument("--timeout", type=int, default=180)
    args = ap.parse_args()

    ddir = os.path.join(args.verdicts, args.debate)
    with open(os.path.join(ddir, "verdict-draft.json")) as f:
        draft = json.load(f)
    with open(args.brief) as f:
        brief = json.load(f)

    # 1. candidates dir for e2e/gate.py (candidate.json shape)
    cand_dir = os.path.join(ddir, "candidates")
    shutil.rmtree(cand_dir, ignore_errors=True)
    os.makedirs(cand_dir)
    for c in brief["candidates"]:
        cj = {"id": c["id"], "task_ref": brief["task_ref"],
              "source": {"kind": "manual", "ref": "oracle-audit"},
              "files": c.get("files"), "patch": c.get("patch"),
              "test_cmd": c.get("test_cmd", "pytest tests -q")}
        with open(os.path.join(cand_dir, c["id"] + ".json"), "w") as f:
            json.dump(cj, f)

    # 2. verdict input for e2e/gate.py (winner + ranking walk order)
    verdict_in = dict(draft)
    verdict_in.pop("anon_map", None)
    verdict_in_path = os.path.join(ddir, "verdict-for-gate.json")
    with open(verdict_in_path, "w") as f:
        json.dump(verdict_in, f)

    # 3. run t3-e2e's gate (owns test execution)
    out_dir = os.path.join(ddir, "gated")
    p = subprocess.run(
        [sys.executable, E2E_GATE, "--verdict", verdict_in_path,
         "--candidates", cand_dir, "--tasks", args.tasks_root,
         "--out", out_dir],
        capture_output=True, text=True, timeout=args.timeout * len(brief["candidates"]) + 60)
    print(p.stdout[-1500:])
    if p.returncode != 0:
        print(p.stderr[-1500:], file=sys.stderr)
        raise SystemExit(f"e2e/gate.py failed (rc={p.returncode})")
    with open(os.path.join(out_dir, "verdict.gated.json")) as f:
        gated = json.load(f)

    # 4. normalize to verdict.json v1 enum + canonical final verdict
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    status = gated["e2e"]["status"]
    if status == "fail":
        status = "failed"  # schema enum; t3-e2e uses "fail" internally
    verdict = {k: gated[k] for k in
               ("debate_id", "task_ref", "winner", "ranking", "confidence",
                "rationale", "judge_model", "judge_prompt_version", "rubric")}
    if "synthesis_map" in gated:
        verdict["synthesis_map"] = gated["synthesis_map"]
    verdict["decided_at"] = now
    e2e = {"status": status,
           "log_ref": gated["e2e"].get("log_ref", "")}
    if gated["e2e"].get("accepted_id"):
        e2e["accepted_id"] = gated["e2e"]["accepted_id"]
    accepted = gated["e2e"].get("accepted_id")

    if accepted is not None:
        if accepted != draft["winner"]:
            verdict["winner"] = accepted  # crown what passed tests
            verdict["rationale"] = (verdict["rationale"] +
                f" [gate: judge winner {draft['winner']} failed e2e; crowned "
                f"{accepted} per ranking cascade]")[:1200]
    else:
        # 5. all failed -> redebate signal (single re-debate, then fail-to-fleet)
        notes = []
        logs = os.path.join(out_dir, "logs")
        for cid in draft["ranking"]:
            lp = os.path.join(logs, cid + ".log")
            try:
                with open(lp) as f:
                    tail = f.read()[-1500:]
            except OSError:
                tail = "(log unreadable)"
            notes.append(f"candidate {cid} FAILED e2e:\n{tail}")
        redebate = {"debate_id": args.debate, "task_ref": brief["task_ref"],
                    "redebate_of": args.debate,
                    "e2e_failure_notes": "\n\n".join(notes)[:4000],
                    "emitted_at": now}
        with open(os.path.join(ddir, "redebate.json"), "w") as f:
            json.dump(redebate, f, indent=2)
        print(f"[gate] ALL CANDIDATES FAILED — redebate.json emitted; "
              f"orchestrator may run ONE re-debate, then fail-to-fleet",
              file=sys.stderr)
    verdict["e2e"] = e2e
    with open(os.path.join(ddir, "verdict.json"), "w") as f:
        json.dump(verdict, f, indent=2)

    # 6. verdict ledger (JSONL): task, debaters, rounds, verdict, test result
    entry = {
        "debate_id": verdict["debate_id"], "task_ref": verdict["task_ref"],
        "debaters": [c["id"] for c in brief["candidates"]],
        "rounds": len({m.get("round") for m in brief.get("transcript", [])}),
        "judge_model": verdict["judge_model"],
        "judge_prompt_version": verdict["judge_prompt_version"],
        "judge_winner": draft["winner"], "crowned": verdict["winner"],
        "confidence": verdict["confidence"],
        "swap_agreement": draft.get("swap_agreement"),
        "e2e_status": status, "accepted_id": accepted, "decided_at": now,
    }
    ledger = os.path.join(args.verdicts, "VERDICTS.jsonl")
    with open(ledger, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(json.dumps({"crowned": verdict["winner"], "e2e": status,
                      "verdict": os.path.join(ddir, "verdict.json"),
                      "ledger": ledger}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
