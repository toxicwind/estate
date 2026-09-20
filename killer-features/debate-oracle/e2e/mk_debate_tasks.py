#!/usr/bin/env python3
"""Build debate-task.json files (schemas/debate-task.json) from generated candidates.

One per task slug -> e2e/debate-tasks/<slug>.json, ready for bin/debate-run
(t3-impl-orchestrator). Unblocks the orchestrator: candidates + lanes + spec.

Usage: mk_debate_tasks.py --tasks TASKS --candidates CAND_DIR --out OUT
"""
import argparse, json, os

HARD_CONSTRAINTS = [
    "winner must pass the hidden pytest acceptance tests for the task (e2e gate is binding)",
    "additive-only: do not break fleet-liveness or existing interfaces",
    "cell-disposable / yote-durable split respected",
    "no eval/exec/compile backdoors where the task bans them",
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--lanes", default=",".join([
        "mradermacher/qwen3.5-9b-deepseek-v4-flash-i1-q4_k_m",
        "beellama/qwen-flash-256k",
        "beellama/exaone-4-0-1-2b-iq4xs",
    ]))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    lanes = a.lanes.split(",")

    for slug in sorted(os.listdir(a.candidates)):
        cand_dir = os.path.join(a.candidates, slug)
        if not os.path.isdir(cand_dir):
            continue
        cands = []
        for fn in sorted(os.listdir(cand_dir)):
            if fn.endswith(".json") and fn != "gen-manifest.json":
                with open(os.path.join(cand_dir, fn)) as f:
                    cands.append(json.load(f))
        if len(cands) < 2:
            print(f"SKIP {slug}: only {len(cands)} candidates")
            continue
        with open(os.path.join(a.tasks, slug, "PROBLEM.md")) as f:
            spec = f.read()
        dt = {
            "task_id": f"debate-{slug}",
            "spec": spec,
            "hard_constraints": HARD_CONSTRAINTS,
            "measured_failure": ("naive single-pass implementations fail hidden edge-case "
                                 "tests: refill math/threading, cycle reporting, O(1) perf "
                                 "gate, no-eval constraint, probabilistic sizing"),
            "candidates": cands[:4],
            "lanes": lanes[:len(cands[:4])],
            "rounds": 3,
            "turn_timeout_s": 120,
            "debate_budget_s": 300,
        }
        with open(os.path.join(a.out, f"{slug}.json"), "w") as f:
            json.dump(dt, f, indent=2)
        print(f"wrote {slug}.json ({len(dt['candidates'])} candidates)")

if __name__ == "__main__":
    main()
