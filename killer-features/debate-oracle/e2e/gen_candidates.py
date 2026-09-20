#!/usr/bin/env python3
"""Generate debate candidates: one implementation per lane per task.

Debaters see ONLY PROBLEM.md (tests stay hidden). Writes candidate.json files
per schemas/candidate.json into --out/<task>/<cid>.json.

Usage: gen_candidates.py --tasks TASKS --out OUT [--only SLUG] [--lanes a,b,c]
"""
import argparse, json, os, sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from llm import chat, extract_python, gen_prompt, GEN_SYSTEM

TASK_MODULE = {
    "token-bucket": "token_bucket.py",
    "toposort": "toposort.py",
    "lru-cache": "lru_cache.py",
    "expr-eval": "expr_eval.py",
    "bloom-filter": "bloom_filter.py",
}
DEFAULT_LANES = [
    "mradermacher/qwen3.5-9b-deepseek-v4-flash-i1-q4_k_m",  # default debater lane
    "beellama/qwen-flash-256k",                            # long-context code lane
    "beellama/exaone-4-0-1-2b-iq4xs",                       # fast / cheap
]
LANE_SHORT = {
    "mradermacher/qwen3.5-9b-deepseek-v4-flash-i1-q4_k_m": "qwen35-9b",
    "beellama/qwen-flash-256k": "qwflash-256k",
    "beellama/exaone-4-0-1-2b-iq4xs": "exaone-12b",
}

def lane_tag(model):
    return LANE_SHORT.get(model, re.sub(r"\W+", "-", model)[:24])

import re

def gen_one(args):
    slug, lane, tasks_dir = args
    with open(os.path.join(tasks_dir, slug, "PROBLEM.md")) as f:
        problem = f.read()
    filename = TASK_MODULE[slug]
    text, latency = chat(lane, GEN_SYSTEM, gen_prompt(filename, problem))
    if text.startswith("__TRANSPORT_ERROR__"):
        return {"slug": slug, "lane": lane, "ok": False, "error": text}
    code = extract_python(text)
    if not code:
        return {"slug": slug, "lane": lane, "ok": False,
                "error": "no python block extracted", "raw_tail": text[-500:]}
    cid = f"t3e2e-{slug}-{lane_tag(lane)}"
    cand = {
        "id": cid,
        "source": {"kind": "manual", "ref": f"t3-e2e lane-gen {lane_tag(lane)}"},
        "task_ref": slug,
        "files": {filename: code},
        "test_cmd": "python -m pytest tests -q",
        "claimed_strengths": [f"single-pass generation via {lane}"],
        "entry_cmd": f"python3 {filename}",
    }
    return {"slug": slug, "lane": lane, "ok": True, "candidate": cand,
            "latency_s": latency}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default=None)
    ap.add_argument("--lanes", default=",".join(DEFAULT_LANES))
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()

    slugs = [a.only] if a.only else sorted(TASK_MODULE.keys())
    lanes = a.lanes.split(",")
    jobs = [(s, lane, a.tasks) for s in slugs for lane in lanes]
    os.makedirs(a.out, exist_ok=True)

    results = []
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for r in ex.map(gen_one, jobs):
            results.append(r)
            slug = r["slug"]
            d = os.path.join(a.out, slug)
            os.makedirs(d, exist_ok=True)
            if r["ok"]:
                with open(os.path.join(d, r["candidate"]["id"] + ".json"), "w") as f:
                    json.dump(r["candidate"], f, indent=2)
                print(f"OK   {slug:13s} {lane_tag(r['lane']):12s} "
                      f"{r['latency_s']:6.1f}s -> {r['candidate']['id']}", flush=True)
            else:
                print(f"FAIL {slug:13s} {lane_tag(r['lane']):12s} :: "
                      f"{r.get('error', '?')[:100]}", flush=True)

    ok = sum(1 for r in results if r["ok"])
    print(f"generated {ok}/{len(results)} candidates")
    with open(os.path.join(a.out, "gen-manifest.json"), "w") as f:
        json.dump([{"slug": r["slug"], "lane": r["lane"], "ok": r["ok"],
                    "latency_s": r.get("latency_s"),
                    "error": r.get("error")} for r in results], f, indent=2)

if __name__ == "__main__":
    main()
