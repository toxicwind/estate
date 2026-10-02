#!/usr/bin/env python3
"""E2E gate (t3-e2e owns): verdict.json + candidate.jsons -> gated verdict.

Usage:
  gate.py --verdict VERDICT.json --candidates CAND_DIR --tasks TASKS_DIR --out OUT_DIR

Contract (ARCHITECTURE.md section 6):
  - walks [winner] + ranking[] in order, first e2e pass wins
  - winner pass      -> e2e.status = "pass", accepted_id = winner
  - runner-up pass   -> e2e.status = "fallback-runner-up", accepted_id = that id
  - all fail         -> e2e.status = "fail" (caller: re-debate or fail-to-fleet)
  - writes OUT_DIR/verdict.gated.json + OUT_DIR/logs/<cid>.log
"""
import argparse, json, os, re, shutil, subprocess, sys, time

VENV_PY = "/home/toxic/sovereign/killer-features/debate-oracle/e2e-venv/bin/python"
GATE_TIMEOUT_S = 180

TASK_MODULE = {
    "token-bucket": "token_bucket.py",
    "toposort": "toposort.py",
    "lru-cache": "lru_cache.py",
    "expr-eval": "expr_eval.py",
    "bloom-filter": "bloom_filter.py",
}

def load_candidates(cand_dir):
    cands = {}
    for fn in os.listdir(cand_dir):
        if fn.endswith(".json"):
            with open(os.path.join(cand_dir, fn)) as f:
                c = json.load(f)
            cands[c["id"]] = c
    return cands

def gate_one(cand, tasks_dir, sandbox):
    """Materialize candidate files, copy hidden tests, run pytest. Returns dict."""
    t0 = time.time()
    task_ref = cand["task_ref"]
    task_dir = os.path.join(tasks_dir, task_ref)
    if os.path.isdir(sandbox):
        shutil.rmtree(sandbox)
    os.makedirs(sandbox)
    files = cand.get("files") or {}
    if not files and cand.get("patch"):
        return {"passed": False, "error": "patch-form candidates not yet supported by gate",
                "latency_s": round(time.time() - t0, 2)}
    for path, content in files.items():
        dest = os.path.join(sandbox, path)
        os.makedirs(os.path.dirname(dest) or sandbox, exist_ok=True)
        with open(dest, "w") as f:
            f.write(content)
    # hidden tests: debaters never saw these
    tests_src = os.path.join(task_dir, "tests")
    if os.path.isdir(tests_src):
        shutil.copytree(tests_src, os.path.join(sandbox, "tests"))
    cmd = [VENV_PY, "-m", "pytest", "tests", "-q"]
    try:
        p = subprocess.run(cmd, cwd=sandbox, capture_output=True, text=True,
                           timeout=GATE_TIMEOUT_S)
        out = (p.stdout or "") + (p.stderr or "")
        passed = p.returncode == 0
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or b"").decode() + (e.stderr or b"").decode() + "\n[TIMEOUT]"
        passed = False
    # summary line: count passed/failed
    m = re.search(r"(\d+) passed", out)
    passed_n = int(m.group(1)) if m else 0
    m = re.search(r"(\d+) failed", out)
    failed_n = int(m.group(1)) if m else 0
    return {"passed": passed, "passed_n": passed_n, "failed_n": failed_n,
            "output_tail": out[-4000:], "latency_s": round(time.time() - t0, 2)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verdict", required=True)
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    with open(a.verdict) as f:
        verdict = json.load(f)
    cands = load_candidates(a.candidates)
    os.makedirs(os.path.join(a.out, "logs"), exist_ok=True)
    os.makedirs(os.path.join(a.out, "sandbox"), exist_ok=True)

    order = []
    for cid in [verdict.get("winner")] + list(verdict.get("ranking", [])):
        if cid and cid != "synthesis" and cid not in order:
            order.append(cid)

    results = {}
    accepted = None
    for i, cid in enumerate(order):
        cand = cands.get(cid)
        if cand is None:
            results[cid] = {"passed": False, "error": "candidate not found"}
            continue
        r = gate_one(cand, a.tasks, os.path.join(a.out, "sandbox", cid))
        results[cid] = r
        with open(os.path.join(a.out, "logs", f"{cid}.log"), "w") as f:
            f.write(r.get("output_tail", ""))
        if r["passed"] and accepted is None:
            accepted = cid
            accepted_rank = i

    if accepted == verdict.get("winner"):
        status = "pass"
    elif accepted:
        status = "fallback-runner-up"
    else:
        status = "fail"

    verdict["e2e"] = {
        "status": status,
        "accepted_id": accepted,
        "log_ref": os.path.join(a.out, "logs"),
        "per_candidate": {cid: {"passed": r["passed"],
                                "passed_n": r.get("passed_n"),
                                "failed_n": r.get("failed_n"),
                                "latency_s": r.get("latency_s"),
                                "error": r.get("error")} for cid, r in results.items()},
    }
    with open(os.path.join(a.out, "verdict.gated.json"), "w") as f:
        json.dump(verdict, f, indent=2)
    print(json.dumps({"status": status, "accepted_id": accepted,
                      "order": order, "results": {k: v["passed"] for k, v in results.items()}},
                     indent=2))

if __name__ == "__main__":
    main()
