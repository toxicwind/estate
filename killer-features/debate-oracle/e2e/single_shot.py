#!/usr/bin/env python3
"""Single-shot baseline (A/B arm 2): ONE lane, ONE direct generation, gate it.

Same prompt shape as candidate generation, no debate, no retries on quality.
Usage: single_shot.py --task SLUG --lane MODEL --tasks TASKS --out OUT
Writes OUT/<slug>.json {candidate, lane, gen_latency_s, gate:{...}}
"""
import argparse, json, os, shutil, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from llm import chat, extract_python, gen_prompt, GEN_SYSTEM

VENV_PY = "/home/toxic/sovereign/killer-features/debate-oracle/e2e-venv/bin/python"
TASK_MODULE = {
    "token-bucket": "token_bucket.py",
    "toposort": "toposort.py",
    "lru-cache": "lru_cache.py",
    "expr-eval": "expr_eval.py",
    "bloom-filter": "bloom_filter.py",
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--lane", required=True)
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    slug = a.task
    os.makedirs(os.path.join(a.out, "code"), exist_ok=True)
    os.makedirs(os.path.join(a.out, "sandbox"), exist_ok=True)
    with open(os.path.join(a.tasks, slug, "PROBLEM.md")) as f:
        problem = f.read()
    filename = TASK_MODULE[slug]

    text, gen_lat = chat(a.lane, GEN_SYSTEM, gen_prompt(filename, problem))
    result = {"task": slug, "lane": a.lane, "gen_latency_s": gen_lat,
              "single_attempt": True}
    if text.startswith("__TRANSPORT_ERROR__"):
        result.update({"ok": False, "error": text})
    else:
        code = extract_python(text)
        if not code:
            result.update({"ok": False, "error": "no python block extracted"})
        else:
            result["ok"] = True
            # gate it: sandbox + hidden tests
            sb = os.path.join(a.out, "sandbox", slug)
            if os.path.isdir(sb):
                shutil.rmtree(sb)
            os.makedirs(sb)
            with open(os.path.join(sb, filename), "w") as f:
                f.write(code)
            with open(os.path.join(a.out, "code", f"{slug}.py"), "w") as f:
                f.write(code)
            shutil.copytree(os.path.join(a.tasks, slug, "tests"),
                            os.path.join(sb, "tests"))
            t0 = time.time()
            try:
                p = subprocess.run([VENV_PY, "-m", "pytest", "tests", "-q"],
                                   cwd=sb, capture_output=True, text=True, timeout=180)
                out = (p.stdout or "") + (p.stderr or "")
                passed = p.returncode == 0
            except subprocess.TimeoutExpired:
                out, passed = "[TIMEOUT]", False
            import re
            mp = re.search(r"(\d+) passed", out); mf = re.search(r"(\d+) failed", out)
            result["gate"] = {"passed": passed,
                              "passed_n": int(mp.group(1)) if mp else 0,
                              "failed_n": int(mf.group(1)) if mf else 0,
                              "latency_s": round(time.time() - t0, 2),
                              "output_tail": out[-3000:]}
            result["total_latency_s"] = round(gen_lat + result["gate"]["latency_s"], 2)

    with open(os.path.join(a.out, f"{slug}.json"), "w") as f:
        json.dump(result, f, indent=2)
    g = result.get("gate", {})
    print(json.dumps({"task": slug, "lane": a.lane, "ok": result["ok"],
                      "gen_s": gen_lat, "gate_passed": g.get("passed"),
                      "passed_n": g.get("passed_n"), "failed_n": g.get("failed_n"),
                      "total_s": result.get("total_latency_s")}, indent=2))

if __name__ == "__main__":
    main()
