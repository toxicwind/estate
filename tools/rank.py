"""Hybrid tool retrieval.

Default: BM25 lexical + field weighting (zero deps).
Optional: FAISS + sentence-transformers if importable.
Combines via reciprocal rank fusion.
"""
from __future__ import annotations
import math, re
from collections import Counter

_TOKEN = re.compile(r"[a-z0-9_]+")
def _tok(s): return _TOKEN.findall((s or "").lower())

class BM25:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs: list[list[str]] = []
        self.df: Counter = Counter()
        self.avgdl = 0.0
    def fit(self, docs: list[str]):
        self.docs = [_tok(d) for d in docs]
        self.df = Counter()
        for toks in self.docs:
            for t in set(toks): self.df[t] += 1
        self.avgdl = sum(len(d) for d in self.docs) / max(1, len(self.docs))
    def score(self, query: str, i: int) -> float:
        q = _tok(query); d = self.docs[i]
        if not d: return 0.0
        dl = len(d); tf = Counter(d); N = len(self.docs)
        s = 0.0
        for t in q:
            if t not in tf: continue
            idf = math.log(1 + (N - self.df[t] + 0.5) / (self.df[t] + 0.5))
            s += idf * (tf[t]*(self.k1+1)) / (tf[t] + self.k1*(1 - self.b + self.b*dl/self.avgdl))
        return s

_FAISS = None
try:
    import numpy as _np
    from sentence_transformers import SentenceTransformer as _ST
    import faiss as _faiss
    _FAISS = _faiss; _ST_MODEL = _ST("sentence-transformers/all-MiniLM-L6-v2")
except Exception:
    _ST_MODEL = None

class Semantic:
    def __init__(self):
        self.index = None; self.vectors = None
    def fit(self, docs: list[str]):
        if _ST_MODEL is None or not docs: return
        self.vectors = _ST_MODEL.encode(docs, normalize_embeddings=True)
        dim = self.vectors.shape[1]
        self.index = _FAISS.IndexFlatIP(dim)
        self.index.add(self.vectors.astype("float32"))
    def score_all(self, query: str) -> list[float]:
        if _ST_MODEL is None or self.index is None: return [0.0]*0
        q = _ST_MODEL.encode([query], normalize_embeddings=True).astype("float32")
        D, _ = self.index.search(q, self.index.ntotal)
        return D[0].tolist()

def rrf(rankings: list[list[int]], k: int = 60) -> dict[int, float]:
    s: dict[int, float] = {}
    for r in rankings:
        for pos, idx in enumerate(r):
            s[idx] = s.get(idx, 0.0) + 1.0/(k + pos + 1)
    return s

def rank_tools(query: str, tools: list[dict], *, top_k: int = 12) -> list[dict]:
    """Return tools re-ranked by hybrid score. Preserves original order on tie."""
    if not tools: return tools
    docs = [f"{t.get('id','')} {t.get('desc','')} {t.get('sig','')}" for t in tools]
    bm = BM25(); bm.fit(docs)
    bm_scores = [bm.score(query, i) for i in range(len(tools))]
    bm_rank = sorted(range(len(tools)), key=lambda i: bm_scores[i], reverse=True)

    sm = Semantic(); sm.fit(docs)
    sem_scores = sm.score_all(query) if sm.index is not None else [0.0]*len(tools)
    sem_rank = sorted(range(len(tools)), key=lambda i: sem_scores[i], reverse=True) if sm.index else []

    fused = rrf([bm_rank] + ([sem_rank] if sem_rank else []))
    order = sorted(range(len(tools)), key=lambda i: fused.get(i, 0.0), reverse=True)

    out = []
    for i in order[:top_k]:
        t = dict(tools[i])
        t["bm25"] = round(bm_scores[i], 4)
        if sem_scores: t["semantic"] = round(sem_scores[i], 4)
        t["fused"] = round(fused.get(i, 0.0), 5)
        out.append(t)
    return out
