#!/usr/bin/env python3
"""auto1m — virtual 1M-context composite route (prototype).

No single model here has a 1M-token window, so this route *composes* one:
oversized inputs are chunked, mapped in parallel across the model fleet via
the sovereign router, and tree-reduced to a single answer with provenance.
When the prompt fits a native 1M model, it routes direct (no map-reduce tax).

Design lineage (repos cloned + read on yote, code-verified):
- thunlp/LLMxMapReduce V1 Generator.py: sentence-aware chunking with
  token-budget accounting (window - prompt - max_tokens), mr_map fan-out,
  mr_collapse tree-collapse loop, mr_reduce with "Information of Chunk N"
  provenance labels.
- THUNLP-MT/ExtAgents pipeline.py: iterative map with info scoring,
  score-sorted selection, exponential candidate counts, early exit.

Hot-path doctrine: race parallel map calls, fail fast per call (120s ceiling,
errors recorded never retried), most query-relevant chunks dispatch first so
partial failure still yields the key facts.
"""

import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Router base: env-overridable. On yote the sovereign router is :25104;
# elsewhere point AUTO1M_ROUTER at whatever OpenAI-compatible router serves.
ROUTER = os.environ.get("AUTO1M_ROUTER", "http://127.0.0.1:25104")
# Worker model for map/score/reduce calls. Default is the task-spec'd
# sovereign/free route; override via env for runs needing a stronger worker,
# e.g. AUTO1M_MODEL=beellama/qwen-flash-256k (the free route currently serves
# a 1.2B local model whose extractions are unreliable — proven 2026-09-21).
MAP_MODEL = os.environ.get("AUTO1M_MODEL", "sovereign/free")
DIRECT_MODEL = os.environ.get("AUTO1M_DIRECT_MODEL", "deepseek/deepseek-v4-pro-0813")  # native ~1M lane; must serve through ROUTER (probe before trusting)
CHUNK_TOKENS = 4000                        # safe for free-tier / local workers
CHUNK_OVERLAP_TOKENS = 200
MAP_WORKERS = int(os.environ.get("AUTO1M_WORKERS", "8"))
CALL_TIMEOUT = 120
DIRECT_BUDGET = 800_000                    # est tokens under which direct lane is tried
REDUCE_BUDGET = 5000                       # est tokens the final reduce may consume
SCORE_BATCH = 12

MAP_PROMPT = (
    "You extract facts. Question: {query}\n"
    "From the text chunk below, copy out ONLY facts that help answer the question.\n"
    "Rules: one fact per line; start each line with [{cid}]; keep each fact short.\n"
    "If nothing in this chunk helps answer, reply with exactly: NO RELEVANT INFO\n"
    "Chunk:\n{chunk}"
)
SCORE_PROMPT = (
    "Question: {query}\n"
    "Rate how relevant each extracted fact is to answering the question, 0-10 "
    "(0 = useless, 10 = directly answers part of it).\n"
    "Reply with one line per fact, format: <number> <score> and nothing else.\n"
    "Facts:\n{facts}"
)
COLLAPSE_PROMPT = (
    "Combine these extracted facts into a short deduplicated bullet list.\n"
    "Keep every [Cxxxx] tag attached to its fact. Drop exact duplicates.\n"
    "Question context: {query}\nFacts:\n{facts}"
)
FINAL_PROMPT = (
    "Answer the question using ONLY the facts below. "
    "Every claim in your answer must cite its chunk like [C0007]. "
    "If the facts do not contain the answer, say what is missing.\n"
    "Question: {query}\nFacts:\n{facts}"
)


def est_tokens(s):
    return len(s) // 4 + 1


def _post_chat(model, messages, max_tokens, timeout):
    """One chat-completions POST. Returns (text, secs, serving_model).
    Raises HTTPError/URLError on failure."""
    payload = json.dumps({"model": model, "messages": messages,
                          "max_tokens": max_tokens}).encode()
    req = urllib.request.Request(
        f"{ROUTER}/v1/chat/completions", data=payload,
        headers={"Content-Type": "application/json"})
    t = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.load(r)
    ch = d["choices"][0]
    return (ch["message"]["content"].strip(), round(time.time() - t, 1),
            str(d.get("model", "?")))


def chat(model, messages, max_tokens=512, timeout=CALL_TIMEOUT):
    # Bounded retry on TRANSIENT errors only (503/429: deploy windows, slot
    # contention). Real errors (400/401/404) fail fast. Proven necessary
    # 2026-09-21: the router 503s in waves during fleet deploys.
    max_attempts = int(os.environ.get("AUTO1M_RETRIES", "3"))
    last = None
    for attempt in range(max_attempts):
        try:
            text, dt, _ = _post_chat(model, messages, max_tokens, timeout)
            return text, dt
        except urllib.error.HTTPError as e:
            if e.code in (503, 429) and attempt < max_attempts - 1:
                last = f"HTTP {e.code}"
                time.sleep(5 * (attempt + 1))
                continue
            raise RuntimeError(f"HTTP {e.code}: {e.read(200)!r}") from e
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
            if attempt < max_attempts - 1:
                time.sleep(5 * (attempt + 1))
                continue
            raise
    raise RuntimeError(f"chat failed after {max_attempts} attempts: {last}")


def split_sentences(text):
    parts = re.split(r"([.!?;\n。！？；])", text)
    sents, buf = [], ""
    for i in range(0, len(parts) - 1, 2):
        s = (parts[i] + parts[i + 1]).strip()
        if s:
            if len(s) > 2000:  # pathological long line: hard split
                sents.extend(s[j:j + 2000] for j in range(0, len(s), 2000))
            else:
                sents.append(s)
    if len(parts) % 2 == 1 and parts[-1].strip():
        tail = parts[-1].strip()
        if len(tail) > 2000:
            sents.extend(tail[j:j + 2000] for j in range(0, len(tail), 2000))
        else:
            sents.append(tail)
    return [s for s in sents if s]


def sentence_spans(text):
    """Map each sentence to its (start, end) span in the source text.

    Sequential search from a running cursor keeps spans monotonic; overlap
    sentences keep their ORIGINAL offsets, so chunk spans honestly overlap
    rather than pointing at synthetic duplicate text.
    """
    spans, cursor = [], 0
    for s in split_sentences(text):
        i = text.find(s, cursor)
        if i < 0:
            i = cursor  # hard-split slices of a >2000-char line may not
                        # match verbatim after strip(); fall back to cursor
        spans.append((s, i, i + len(s)))
        cursor = i + len(s)
    return spans


def chunk_text(text, source, chunk_tokens=CHUNK_TOKENS,
               overlap_tokens=CHUNK_OVERLAP_TOKENS, start_id=0):
    """Sentence-aware chunks with token budget + overlap. Returns chunk dicts.

    start/end are spans into the ORIGINAL source text (via sentence_spans).
    Overlap sentences keep their original offsets, so consecutive chunk spans
    honestly overlap instead of pointing at synthetic duplicate text.
    """
    spans = sentence_spans(text)  # (sentence, start, end)
    chunks, cur, cur_tok, cid = [], [], 0, start_id
    for s, ss, se in spans:
        st = est_tokens(s)
        if cur and cur_tok + st > chunk_tokens:
            chunks.append({"id": f"C{cid:04d}", "source": source,
                           "start": cur[0][1], "end": cur[-1][2],
                           "text": " ".join(x[0] for x in cur)})
            cid += 1
            # overlap: carry trailing sentences worth ~overlap_tokens
            ov, ov_tok = [], 0
            for ps in reversed(cur):
                pt = est_tokens(ps[0])
                if ov_tok + pt > overlap_tokens:
                    break
                ov.insert(0, ps)
                ov_tok += pt
            cur, cur_tok = ov, ov_tok
        cur.append((s, ss, se))
        cur_tok += st
    if cur:
        chunks.append({"id": f"C{cid:04d}", "source": source,
                       "start": cur[0][1], "end": cur[-1][2],
                       "text": " ".join(x[0] for x in cur)})
    return chunks


def query_terms(query):
    return [w.lower() for w in re.findall(r"[a-zA-Z0-9][a-zA-Z0-9\-./]{2,}", query)]


def rank_chunks(chunks, query):
    """Query-aware ordering: keyword-overlap score, most relevant maps first."""
    terms = query_terms(query)
    scored = []
    for c in chunks:
        low = c["text"].lower()
        score = sum(low.count(t) for t in terms)
        scored.append((score, c))
    scored.sort(key=lambda x: -x[0])
    return [c for _, c in scored]


def map_extract(chunk, query):
    prompt = MAP_PROMPT.format(query=query, cid=chunk["id"], chunk=chunk["text"])
    try:
        out, dt = chat(MAP_MODEL, [{"role": "user", "content": prompt}],
                       max_tokens=512)
    except Exception as e:
        return {"chunk": chunk, "ok": False, "error": f"{type(e).__name__}: {e}"}
    if "NO RELEVANT INFO" in out.upper():
        return {"chunk": chunk, "ok": True, "empty": True, "secs": dt}
    facts = [l.strip() for l in out.splitlines()
             if l.strip() and not l.strip().upper().startswith("NO RELEVANT")]
    return {"chunk": chunk, "ok": True, "facts": facts, "secs": dt}


def score_facts(facts, query):
    """Batched LLM relevance scoring (ExtAgents-style). Falls back to keyword order."""
    if not facts:
        return []
    terms = query_terms(query)
    scored = []
    for i in range(0, len(facts), SCORE_BATCH):
        batch = facts[i:i + SCORE_BATCH]
        listed = "\n".join(f"{n + 1}. {f}" for n, f in enumerate(batch))
        try:
            out, _ = chat(MAP_MODEL, [{"role": "user",
                                       "content": SCORE_PROMPT.format(query=query, facts=listed)}],
                           max_tokens=256)
            for line in out.splitlines():
                m = re.match(r"\s*(\d+)\s+(\d+)", line)
                if m:
                    n, s = int(m.group(1)) - 1, int(m.group(2))
                    if 0 <= n < len(batch):
                        scored.append((min(max(s, 0), 10), batch[n]))
            got = {f for _, f in scored[-len(batch):]}
            for f in batch:  # unscored -> keyword fallback
                if f not in got:
                    low = f.lower()
                    scored.append((sum(low.count(t) for t in terms), f))
        except Exception:
            for f in batch:
                low = f.lower()
                scored.append((sum(low.count(t) for t in terms), f))
    scored.sort(key=lambda x: -x[0])
    return [f for _, f in scored]


def collapse_once(facts, query):
    """One tree-collapse level: group facts into budget-fitting batches, collapse in parallel."""
    batches, cur, cur_tok = [], [], 0
    for f in facts:
        ft = est_tokens(f)
        if cur and cur_tok + ft > REDUCE_BUDGET:
            batches.append(cur)
            cur, cur_tok = [], 0
        cur.append(f)
        cur_tok += ft
    if cur:
        batches.append(cur)
    if len(batches) <= 1:
        return facts

    def _collapse(batch):
        try:
            out, _ = chat(MAP_MODEL, [{"role": "user", "content": COLLAPSE_PROMPT.format(
                query=query, facts="\n".join(batch))}], max_tokens=1024)
            return [l.strip() for l in out.splitlines()
                    if l.strip() and re.search(r"\[C\d+\]", l)]
        except Exception as e:
            return batch  # fail-open: keep uncollapsed rather than lose facts

    out = []
    with ThreadPoolExecutor(max_workers=MAP_WORKERS) as ex:
        futs = [ex.submit(_collapse, b) for b in batches]
        for f in futs:
            out.extend(f.result())
    return out


def tree_reduce(facts, query, max_levels=6):
    level = 0
    while est_tokens("\n".join(facts)) > REDUCE_BUDGET and level < max_levels:
        facts = collapse_once(facts, query)
        level += 1
    return facts


def rewrite_dangling_citations(text, prov):
    """Rewrite any [Cxxxx] citation not in the provenance map to the nearest
    real chunk id (fail-closed: no fabricated ids survive). Returns
    (fixed_text, dangling_tags)."""
    valid = set(prov)
    dangling = []

    def repl(m):
        tag = f"C{m.group(1)}"
        if tag in valid:
            return m.group(0)
        dangling.append(tag)
        nums = sorted(int(x[1:]) for x in valid)
        n = int(m.group(1))
        best = min(nums, key=lambda x: abs(x - n)) if nums else 0
        return f"[C{best:04d}]"

    return re.sub(r"\[C(\d{4})\]", repl, text), sorted(set(dangling))


def answer_question(query, corpus_text=None, sources=None, force_composite=False):
    """Main entry. Returns dict(answer, provenance, stats, lane).

    sources: optional [(text, label)] multi-file input — each doc keeps its
    own provenance label and chunk ids stay globally unique across docs.
    (corpus_text is kept for the single-text call path; label "corpus".)
    """
    if sources is None:
        sources = [(corpus_text or "", "corpus")]
    t0 = time.time()
    total = sum(est_tokens(t) for t, _ in sources) + est_tokens(query)

    # Direct lane: prompt fits a native 1M model -> one call, no map-reduce tax.
    if not force_composite and total <= DIRECT_BUDGET:
        joined = "\n\n".join(f"### SOURCE: {lab}\n{t}" for t, lab in sources)
        try:
            out, dt = chat(DIRECT_MODEL,
                           [{"role": "user",
                             "content": f"Answer the question using the corpus below. "
                                        f"Cite sources.\nQuestion: {query}\nCorpus:\n{joined}"}],
                           max_tokens=2048, timeout=600)
            return {"answer": out, "lane": f"direct:{DIRECT_MODEL}",
                    "provenance": [{"chunk": "FULL", "source": "direct-pass"}],
                    "stats": {"secs": round(time.time() - t0, 1),
                              "est_tokens": total, "chunks": 1}}
        except Exception as e:
            sys.stderr.write(f"direct lane failed ({e}); falling back to composite\n")

    # Composite lane
    chunks, cid = [], 0
    for text, label in sources:
        cs = chunk_text(text, source=label, start_id=cid)
        chunks.extend(cs)
        cid += len(cs)
    ordered = rank_chunks(chunks, query)
    stats = {"est_tokens": total, "chunks": len(chunks)}

    t_map = time.time()
    results = []
    with ThreadPoolExecutor(max_workers=MAP_WORKERS) as ex:
        futs = {ex.submit(map_extract, c, query): c for c in ordered}
        for fut in as_completed(futs):
            results.append(fut.result())
    stats["map_secs"] = round(time.time() - t_map, 1)

    ok = [r for r in results if r.get("ok") and not r.get("empty")]
    failed = [r for r in results if not r.get("ok")]
    empty = [r for r in results if r.get("ok") and r.get("empty")]
    stats.update({"mapped_ok": len(ok), "mapped_empty": len(empty),
                  "mapped_failed": len(failed)})
    if failed:
        sys.stderr.write(f"map failures: {len(failed)} e.g. {failed[0].get('error')}\n")
    facts = [f for r in ok for f in r.get("facts", [])]
    if not facts:
        return {"answer": "NO RELEVANT INFO in corpus.", "lane": "composite",
                "provenance": [], "stats": stats}

    t_red = time.time()
    facts = score_facts(facts, query)
    stats["facts_scored"] = len(facts)
    facts = tree_reduce(facts, query)
    stats["facts_after_collapse"] = len(facts)
    lane = "composite:chunk-map-tree-reduce"
    try:
        final, _ = chat(MAP_MODEL, [{"role": "user", "content": FINAL_PROMPT.format(
            query=query, facts="\n".join(facts))}], max_tokens=1024)
    except Exception as e:
        # Fail-open: a dead final call must not lose the extracted evidence.
        sys.stderr.write(f"final answer call failed ({e}); returning collapsed facts\n")
        final = ("[degraded: final synthesis unavailable] Relevant extracted facts:\n"
                 + "\n".join(facts))
        lane = "composite:chunk-map-tree-reduce:final-degraded"
    stats["reduce_secs"] = round(time.time() - t_red, 1)

    prov = {}
    for r in ok:
        c = r["chunk"]
        prov[c["id"]] = {"source": c["source"], "start": c["start"], "end": c["end"]}
    stats["secs"] = round(time.time() - t0, 1)

    # Validate final citations against the provenance map: never let the model
    # fabricate a [Cxxxx] tag (e.g. the 1.2B invented [C0126]). Rewrite any
    # dangling tag to the nearest real chunk and record the correction.
    final, dangling_tags = rewrite_dangling_citations(final, prov)
    if dangling_tags:
        stats["dangling_citations_rewritten"] = dangling_tags

    return {"answer": final, "lane": lane,
            "provenance": prov, "stats": stats}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="auto1m virtual 1M-context route")
    ap.add_argument("--query", required=True)
    ap.add_argument("--corpus", required=True, help="text file (or dir of .md files)")
    ap.add_argument("--force-composite", action="store_true")
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    import os
    if os.path.isdir(a.corpus):
        parts = []
        for root, _, files in os.walk(a.corpus):
            for fn in sorted(files):
                if fn.endswith(".md"):
                    p = os.path.join(root, fn)
                    parts.append(f"\n\n===== FILE: {p} =====\n" +
                                 open(p, encoding="utf-8", errors="replace").read())
        corpus = "".join(parts)
    else:
        corpus = open(a.corpus, encoding="utf-8", errors="replace").read()

    res = answer_question(a.query, corpus, force_composite=a.force_composite)
    report = {"query": a.query, "answer": res["answer"], "lane": res["lane"],
              "stats": res["stats"],
              "provenance": res["provenance"] if isinstance(res["provenance"], dict)
              else res["provenance"]}
    text = json.dumps(report, indent=2)
    if a.out:
        open(a.out, "w").write(text)
        print(f"wrote {a.out}")
    print(text[:6000])
