#!/usr/bin/env python3
"""Full proof: auto1m over the real fleet corpus (~700k tokens) on yote.

Three cross-document questions. Every EXPECT needle was grep-verified in the
actual corpus files (2026-09-21) — no aspirational needles:

  Q1: ROUTER.md -> yote hardware ("16 cores", "62 GB", "RTX 3090")
  Q2: docs/fleet-knowledgebase.md 1m-prober row -> "nemotron-3-super-120b-a12b",
      "49c17bb9fd", "41.4s"
  Q3: corpus/completions-internal.md (fetched 2026-09-21 from the canonical
      toxicwind/hatch-docs repo, runtime/completions-internal.md) ->
      "Muse Spark", "200,000 tokens"

Pass bar: composite lane chosen, all questions answered, every [Cxxxx]
citation resolves in the provenance map, no dangling citations, EXPECT
needles present. Writes test-evidence.json.
"""
import json
import os
import re
import sys
import time
import urllib.request

ROUTER = os.environ.get("AUTO1M_ROUTER", "http://127.0.0.1:25104")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auto1m import answer_question, est_tokens

HERE = os.path.dirname(os.path.abspath(__file__))

# Corpus: targeted question files + real doc trees for ~700k-token weight.
# Every EXPECT needle is grep-verified in its file (2026-09-21).
CORPUS_DIRS = [
    "/home/toxic/sovereign/docs",              # KB + estate docs (Q1, Q2 live here)
    "/home/toxic/sovereign/projects/tau/docs",  # corpus weight (~2.5M chars)
]
CORPUS_EXTRA_FILES = [
    os.path.join(HERE, "corpus", "completions-internal.md"),  # Q3 lives here
]

QUESTIONS = [
    ("What are yote's hardware specs?",
     ["16 cores", "62 GB", "RTX 3090"]),
    ("What did the 1m-prober long-context probe achieve, which model passed "
     "the 1M needle retrieval, and which commit records its results?",
     ["nemotron-3-super-120b-a12b", "49c17bb9fd", "41.4s"]),
    ("What model serves this conversation per the completions internals doc, "
     "and what is its context window?",
     ["Muse Spark", "200,000 tokens"]),
]

# Hard requirements on corpus files (fail fast if the corpus isn't real)
NEEDLE_FILES = {
    "16 cores": "/home/toxic/sovereign/docs/fleet-knowledgebase.md",
    "62 GB": "/home/toxic/sovereign/docs/fleet-knowledgebase.md",
    "RTX 3090": "/home/toxic/sovereign/docs/fleet-knowledgebase.md",
    "nemotron-3-super-120b-a12b": "/home/toxic/sovereign/docs/fleet-knowledgebase.md",
    "49c17bb9fd": "/home/toxic/sovereign/docs/fleet-knowledgebase.md",
    "41.4s": "/home/toxic/sovereign/docs/fleet-knowledgebase.md",
    "Muse Spark": os.path.join(HERE, "corpus", "completions-internal.md"),
    "200,000 tokens": os.path.join(HERE, "corpus", "completions-internal.md"),
}
for needle, path in NEEDLE_FILES.items():
    if not os.path.isfile(path):
        sys.exit("corpus file missing: " + path)
    if needle not in open(path, errors="replace").read():
        sys.exit(f"needle {needle!r} NOT in {path} -- corpus changed, fix test")


def check_router(timeout=600):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            req = urllib.request.Request(
                ROUTER + "/v1/chat/completions",
                data=json.dumps({"model": os.environ.get("AUTO1M_MODEL", "sovereign/free"),
                                 "messages": [{"role": "user", "content": "Reply with exactly: READY"}],
                                 "max_tokens": 8}).encode(),
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                d = json.load(r)
                txt = d["choices"][0]["message"]["content"]
                if "READY" in txt.upper():
                    print(f"router+worker ready after {time.time()-t0:.0f}s "
                          f"(serving={d.get('model')})")
                    return d.get("model")
        except Exception as e:
            print("router probe:", type(e).__name__, str(e)[:100])
        time.sleep(20)
    sys.exit("router never became ready")


def main():
    serving_model = check_router()
    # multi-source input: every real .md keeps its own provenance label
    seen, sources = set(), []
    for d in CORPUS_DIRS:
        for root, _, files in os.walk(d):
            for fn in sorted(files):
                if not fn.endswith(".md"):
                    continue
                p = os.path.join(root, fn)
                if p in seen:
                    continue
                seen.add(p)
                with open(p, errors="replace") as f:
                    sources.append((f.read(), p))
    for p in CORPUS_EXTRA_FILES:
        if p in seen:
            continue
        seen.add(p)
        with open(p, errors="replace") as f:
            sources.append((f.read(), p))
    total = sum(len(t) for t, _ in sources)
    print(f"corpus: {len(sources)} files, {total} chars, ~{total//4} est tokens")

    t0 = time.time()
    results, prov = [], {}
    for qi, (q, expect) in enumerate(QUESTIONS):
        res = answer_question(q, sources=sources, force_composite=True)
        prov.update(res["provenance"])
        results.append({"question": q, "expect": expect,
                        "answer": res["answer"], "lane": res["lane"],
                        "stats": res["stats"]})
        print(f"---- Q{qi+1} ANSWER ----\n{res['answer']}\n")
    wall = time.time() - t0
    print(f"wall: {wall:.1f}s")

    # --- assertions ---
    fails = []
    for r in results:
        for phrase in r["expect"]:
            if phrase.lower() not in r["answer"].lower():
                fails.append(f"Q missing: {phrase!r}")
    # citations must all resolve in the provenance map
    cited = set()
    for r in results:
        cited |= set(re.findall(r"\[C(\d{4})\]", r["answer"]))
    dangling = sorted(c for c in cited if f"C{c}" not in prov)
    if dangling:
        fails.append(f"dangling citations: {dangling}")
    # cross-file: citations must span at least 2 distinct source files
    cited_sources = {prov[f"C{c}"]["source"] for c in cited if f"C{c}" in prov}
    if len(cited_sources) < 2:
        fails.append(f"citations span only {len(cited_sources)} source file(s): "
                     f"{sorted(cited_sources)}")
    # lane must be composite for all questions
    for r in results:
        if not r["lane"].startswith("composite"):
            fails.append(f"lane not composite for: {r['question'][:40]}")

    evidence = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "router": ROUTER,
        "serving_model": serving_model,
        "worker": os.environ.get("AUTO1M_MODEL", "sovereign/free"),
        "corpus_files": CORPUS_DIRS + CORPUS_EXTRA_FILES,
        "corpus_sources": len(sources),
        "est_tokens": sum(est_tokens(t) for t, _ in sources),
        "wall_secs": round(wall, 1),
        "questions": [{"q": r["question"], "lane": r["lane"],
                       "stats": r["stats"],
                       "expect": r["expect"],
                       "missing": [p for p in r["expect"]
                                   if p.lower() not in r["answer"].lower()],
                       "answer": r["answer"]} for r in results],
        "citations_found": sorted(cited),
        "dangling": dangling,
        "verdict": "PASS" if not fails else "FAIL",
        "failures": fails,
    }
    ep = os.path.join(HERE, "test-evidence.json")
    json.dump(evidence, open(ep, "w"), indent=2)
    print("wrote", ep)
    if fails:
        print("FAIL:")
        for f in fails:
            print(" -", f)
        sys.exit(1)
    print("PASS: composite proof over real corpus, citations all resolve")


if __name__ == "__main__":
    main()
