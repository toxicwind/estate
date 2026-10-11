"""ML/text analysis on the HAR clipboard corpus. Writes FINDINGS.md + CSVs."""
import json, os, re, base64, math
import pandas as pd
import numpy as np
from scipy import sparse
from collections import Counter

OUT = "/home/toxic/analysis-clipboard-20260914"
FILES = {
    "A": "/home/toxic/projects/portal-audit/raw/user_pasted_clipboard_long_content_as_file_{ log { ve.txt",
    "B": "/home/toxic/projects/portal-audit/raw/user_pasted_clipboard_long_content_as_file_{ log { ve(1).txt",
}
df = pd.read_csv(os.path.join(OUT, "har_entries_all.csv"))

def tok(s):
    return re.findall(r"[a-z0-9]{2,}", str(s).lower())

def tfidf(docs, max_f=8000, min_df=2):
    tf = [Counter(tok(d)) for d in docs]
    dfc = Counter()
    for c in tf:
        for t in c:
            dfc[t] += 1
    vocab = {t: i for i, (t, c) in enumerate(dfc.items()) if c >= min_df}
    vocab = dict(sorted(vocab.items(), key=lambda kv: -dfc[kv[0]])[:max_f])
    vocab = {t: i for i, t in enumerate(vocab)}
    N = len(docs)
    rows, cols, data = [], [], []
    for di, c in enumerate(tf):
        tot = sum(c.values()) or 1
        for t, f in c.items():
            if t in vocab:
                idf = math.log(N / dfc[t])
                rows.append(di); cols.append(vocab[t]); data.append(f / tot * idf)
    X = sparse.csr_matrix((data, (rows, cols)), shape=(len(docs), len(vocab)))
    Xn = sparse.diags(1.0 / np.maximum(X.multiply(X).sum(1).A.ravel() ** 0.5, 1e-12)) @ X
    inv = {i: t for t, i in vocab.items()}
    return Xn, inv, dfc

def kmeans(X, k, iters=25, seed=7):
    rng = np.random.default_rng(seed)
    n = X.shape[0]
    first = rng.integers(n)
    C = [X[first].toarray().ravel()]
    for _ in range(1, k):
        sims = X @ np.array(C).T
        best = np.asarray(sims.max(1)).ravel()
        d2 = np.maximum(1.0 - best, 0.0)
        tot = d2.sum()
        nxt = rng.integers(n) if tot <= 0 else rng.choice(n, p=d2 / tot)
        C.append(X[nxt].toarray().ravel())
    C = np.array(C)
    C = C / np.maximum(np.linalg.norm(C, axis=1, keepdims=True), 1e-12)
    lab = np.zeros(n, int)
    for _ in range(iters):
        s = X @ C.T
        lab = np.asarray(s.argmax(1)).ravel()
        newC = np.zeros_like(C)
        for j in range(k):
            m = X[lab == j]
            if m.shape[0]:
                v = np.asarray(m.sum(0)).ravel()
                newC[j] = v / max(np.linalg.norm(v), 1e-12)
            else:
                newC[j] = C[j]
        if np.allclose(newC, C):
            C = newC
            break
        C = newC
    return lab, C

def top_terms(C, inv, n=10):
    out = []
    for j in range(C.shape[0]):
        idx = np.argsort(-C[j])[:n]
        out.append([(inv[i], round(float(C[j][i]), 3)) for i in idx])
    return out

# ---------- corpus 1: endpoint docs ----------
ep_docs = (df["method"].fillna("") + " " + df["host"].fillna("") + " " +
           df["path"].fillna("") + " " + df["service"].fillna(""))
Xe, inv_e, _ = tfidf(ep_docs.tolist())
lab_e, Ce = kmeans(Xe, 8)
df["ep_cluster"] = lab_e
ep_terms = top_terms(Ce, inv_e)

# ---------- corpus 2: body texts ----------
bodies, bmeta = [], []
TEXTMIME = ("text", "json", "javascript", "xml")
for tag, f in FILES.items():
    with open(f, encoding="utf-8", errors="replace") as fh:
        data = json.load(fh)
    for i, e in enumerate(data["log"]["entries"]):
        c = (e.get("response", {}).get("content", {}) or {})
        t = c.get("text") or ""
        if not t:
            continue
        if c.get("encoding") == "base64":
            try:
                t = base64.b64decode(t[:200000]).decode("utf-8", "replace")
            except Exception:
                continue
        mime = (c.get("mimeType") or "").lower()
        if not any(x in mime for x in TEXTMIME):
            continue
        bodies.append(t[:3000])
        bmeta.append({"file_tag": tag, "entry_idx": i,
                      "url": e["request"]["url"][:160],
                      "mime": c.get("mimeType"), "status": e["response"].get("status")})
print("textual bodies:", len(bodies))
Xb, inv_b, _ = tfidf(bodies)
lab_b, Cb = kmeans(Xb, 6)
b_terms = top_terms(Cb, inv_b)
bdf = pd.DataFrame(bmeta); bdf["body_cluster"] = lab_b
bdf.to_csv(os.path.join(OUT, "body_clusters.csv"), index=False)

# ---------- timeline ----------
df["started_dt"] = pd.to_datetime(df["started"])
df["t10s"] = df["started_dt"].dt.floor("10s")
tl = df.groupby("t10s").size()

# ---------- anomalies ----------
slow = df.nlargest(10, "time_ms")[["file_tag", "method", "host", "path", "time_ms", "status"]]
big = df.nlargest(10, "body_len")[["file_tag", "host", "path", "mime", "body_len", "status"]]
err = df[df["status"] == 0][["file_tag", "method", "host", "path", "time_ms"]]
ws = df[df["status"] == 101][["file_tag", "host", "path"]]

# ---------- krabby + memory_id mining ----------
krab_hits = []
memrecs = []
mempat = re.compile(r'\{[^{}]*"memory_id"\s*:\s*"(\d+)"[^{}]*"date"\s*:\s*"([^"]+)"[^{}]*"content"\s*:\s*"((?:[^"\\]|\\.){0,400})')
for tag, f in FILES.items():
    with open(f, encoding="utf-8", errors="replace") as fh:
        raw = fh.read()
    for m in re.finditer(r"(?i).{80}krabby.{80}", raw):
        krab_hits.append({"file_tag": tag, "ctx": m.group(0)[:220].replace("\n", " ")})
    for m in mempat.finditer(raw):
        memrecs.append({"file_tag": tag, "memory_id": m.group(1), "date": m.group(2),
                        "content_head": m.group(3)[:200]})
memdf = pd.DataFrame(memrecs).drop_duplicates()
memdf.to_csv(os.path.join(OUT, "memory_records.csv"), index=False)
print("krabby hits:", len(krab_hits), "memory recs:", len(memrecs), "unique:", len(memdf))

for h in krab_hits[:10]:
    print("KRABBY:", h["file_tag"], h["ctx"][:160])
