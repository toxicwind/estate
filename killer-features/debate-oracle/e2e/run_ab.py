#!/usr/bin/env python3
"""A/B driver (t3-e2e): single-shot baseline vs full debate, per task.

Usage:
  run_ab.py --tasks TASKS --root E2E_ROOT [--redo-single] [--debate-only] [--single-only]
            [--debate-bin PATH] [--lane MODEL]

Steps per task slug:
  1. single-shot: single_shot.py (unless result exists and not --redo-single)
  2. debate: if --debate-bin exists -> bin/debate-run --task debate-tasks/<slug>.json
     -> verdict.json -> gate.py walks winner+ranking -> gated verdict
  3. appends per-task row to results/ab.json (JSONL-ish dict)

The debate arm waits for t3-impl-orchestrator's bin/debate-run; run with
--single-only until it lands.
"""
import argparse, json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
VENV_PY = "/home/toxic/sovereign/killer-features/debate-oracle/e2e-venv/bin/python"
SINGLE_LANE = "mradermacher/qwen3.5-9b-deepseek-v4-flash-i1-q4_k_m"
TASKS = ["token-bucket", "toposort", "lru-cache", "expr-eval", "bloom-filter"]

def run(cmd, **kw):
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=kw.get("timeout", 900))
    return p

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--lane", default=SINGLE_LANE)
    ap.add_argument("--debate-bin", default=None)
    ap.add_argument("--redo-single", action="store_true")
    ap.add_argument("--single-only", action="store_true")
    ap.add_argument("--debate-only", action="store_true")
    a = ap.parse_args()

    res_path = os.path.join(a.root, "results", "ab.json")
    os.makedirs(os.path.dirname(res_path), exist_ok=True)
    results = {}
    if os.path.exists(res_path):
        with open(res_path) as f:
            results = json.load(f)

    for slug in TASKS:
        row = results.get(slug, {"task": slug})
        # ---- arm 1: single-shot
        if not a.debate_only:
            ss_out = os.path.join(a.root, "single-shot")
            ss_json = os.path.join(ss_out, f"{slug}.json")
            if a.redo_single or not os.path.exists(ss_json):
                print(f"[{slug}] single-shot via {a.lane} ...", flush=True)
                p = run([VENV_PY, os.path.join(HERE, "single_shot.py"),
                         "--task", slug, "--lane", a.lane,
                         "--tasks", a.tasks, "--out", ss_out], timeout=600)
                print(p.stdout[-600:] + p.stderr[-600:])
            with open(ss_json) as f:
                ss = json.load(f)
            row["single_shot"] = {
                "lane": ss.get("lane"), "ok": ss.get("ok"),
                "gen_latency_s": ss.get("gen_latency_s"),
                "gate_passed": (ss.get("gate") or {}).get("passed"),
                "passed_n": (ss.get("gate") or {}).get("passed_n"),
                "failed_n": (ss.get("gate") or {}).get("failed_n"),
                "total_latency_s": ss.get("total_latency_s"),
                "error": ss.get("error"),
            }
        # ---- arm 2: debate
        if not a.single_only and a.debate_bin and os.path.exists(a.debate_bin):
            dt = os.path.join(a.root, "debate-tasks", f"{slug}.json")
            ddir = os.path.join(a.root, "debates", slug)
            os.makedirs(ddir, exist_ok=True)
            print(f"[{slug}] debate via {a.debate_bin} ...", flush=True)
            t0 = time.time()
            p = run([a.debate_bin, "--task", dt, "--out", ddir], timeout=600)
            debate_s = round(time.time() - t0, 2)
            print(p.stdout[-800:] + p.stderr[-800:])
            verdict = os.path.join(ddir, "verdict.json")
            if os.path.exists(verdict):
                gdir = os.path.join(ddir, "gate")
                p2 = run([VENV_PY, os.path.join(HERE, "gate.py"),
                          "--verdict", verdict,
                          "--candidates", os.path.join(a.root, "candidates", slug),
                          "--tasks", a.tasks, "--out", gdir], timeout=900)
                print(p2.stdout[-800:])
                with open(os.path.join(gdir, "verdict.gated.json")) as f:
                    gv = json.load(f)
                row["debate"] = {
                    "debate_latency_s": debate_s,
                    "winner": gv.get("winner"),
                    "confidence": gv.get("confidence"),
                    "judge_model": gv.get("judge_model"),
                    "e2e_status": (gv.get("e2e") or {}).get("status"),
                    "accepted_id": (gv.get("e2e") or {}).get("accepted_id"),
                    "per_candidate": (gv.get("e2e") or {}).get("per_candidate"),
                }
            else:
                row["debate"] = {"error": "no verdict.json produced",
                                 "debate_latency_s": debate_s}
        elif not a.single_only:
            row.setdefault("debate", {"status": "waiting-for-bin/debate-run"})
        results[slug] = row
        with open(res_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"[{slug}] row saved", flush=True)

    print(f"results -> {res_path}")

if __name__ == "__main__":
    main()
