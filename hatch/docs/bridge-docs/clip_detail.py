"""Self-contained details printer: endpoint clusters + timeline + anomalies."""
import os, re, math
import pandas as pd
import numpy as np
from scipy import sparse
from collections import Counter

OUT = "/home/toxic/analysis-clipboard-20260914"
df = pd.read_csv(os.path.join(OUT, "har_entries_all.csv"))
bdf = pd.read_csv(os.path.join(OUT, "body_clusters.csv"))

def tok(s):
    return re.findall(r"[a-z0-9]{2,}", str(s).lower())

def tfidf(docs, max_f=8000, min_df=2):
    tf = [Counter(tok(d)) for d in docs]
    dfc = Counter()
    for c in tf:
        for t in c:
            dfc[t] += 1
    vocab = {t: i for i, t in enumerate(sorted([t for t, c in dfc.items() if c >= min_df],
                        key=lambda t: -dfc[t])[:max_f])}
    N = len(docs)
    rows, cols, data = [], [], []
    for di, c in enumerate(tf):
        tot = sum(c.values()) or 1
        for t, f in c.items():
            if t in vocab:
                rows.append(di); cols.append(vocab[t])
                data.append(f / tot * math.log(N / dfc[t]))
    X = sparse.csr_matrix((data, (rows, cols)), shape=(len(docs), len(vocab)))
    nrm = np.maximum((X.multiply(X).sum(1).A.ravel()) ** 0.5, 1e-12)
    return (sparse.diags(1.0 / nrm) @ X), {i: t for t, i in vocab.items()}

def kmeans(X, k, iters=25, seed=7):
    rng = np.random.default_rng(seed); n = X.shape[0]
    C = [X[rng.integers(n)].toarray().ravel()]
    for _ in range(1, k):
        best = np.asarray((X @ np.array(C).T).max(1)).ravel()
        d2 = np.maximum(1.0 - best, 0.0); tot = d2.sum()
        C.append(X[rng.integers(n) if tot <= 0 else rng.choice(n, p=d2 / tot)].toarray().ravel())
    C = np.array(C); C /= np.maximum(np.linalg.norm(C, axis=1, keepdims=True), 1e-12)
    lab = np.zeros(n, int)
    for _ in range(iters):
        lab = np.asarray((X @ C.T).argmax(1)).ravel()
        nC = np.zeros_like(C)
        for j in range(k):
            m = X[lab == j]
            if m.shape[0]:
                v = np.asarray(m.sum(0)).ravel(); nC[j] = v / max(np.linalg.norm(v), 1e-12)
            else:
                nC[j] = C[j]
        if np.allclose(nC, C): C = nC; break
        C = nC
    return lab, C

ep_docs = (df["method"].fillna("") + " " + df["host"].fillna("") + " " +
           df["path"].fillna("") + " " + df["service"].fillna(""))
Xe, inv_e = tfidf(ep_docs.tolist())
lab_e, Ce = kmeans(Xe, 8)
df["ep_cluster"] = lab_e
df.to_csv(os.path.join(OUT, "har_entries_all.csv"), index=False)

print("=== ENDPOINT CLUSTERS (n=8) ===")
for j in range(8):
    sub = df[df["ep_cluster"] == j]
    terms = [(inv_e[i], round(float(Ce[j][i]), 2)) for i in np.argsort(-Ce[j])[:8]]
    print("C%d n=%d terms=%s" % (j, len(sub), [t for t, _ in terms]))
    print("    hosts:", sub["host"].value_counts().head(3).to_dict())
    print("    paths:", {p[:60]: c for p, c in sub["path"].value_counts().head(4).items()})

print()
print("=== BODY CLUSTERS (n=6) sample urls ===")
for j in sorted(bdf["body_cluster"].unique()):
    sub = bdf[bdf["body_cluster"] == j]
    print("B%d n=%d mimes=%s" % (j, len(sub), sub["mime"].value_counts().head(2).to_dict()))
    for u in sub["url"].str[:80].value_counts().head(3).index:
        print("    -", u)

print()
print("=== TIMELINE (10s) ===")
df["started_dt"] = pd.to_datetime(df["started"])
print(df.groupby(df["started_dt"].dt.floor("10s")).size().to_string())
print()
print("=== STATUS 0 ==="); print(df[df["status"] == 0][["file_tag", "method", "host", "path"]].to_string())
print()
print("=== SLOWEST 8 ==="); print(df.nlargest(8, "time_ms")[["file_tag", "host", "path", "time_ms", "status"]].to_string())
print()
print("=== LARGEST 8 bodies ==="); print(df.nlargest(8, "body_len")[["file_tag", "host", "path", "mime", "body_len"]].to_string())
print()
print("=== WS 101 ==="); print(df[df["status"] == 101][["file_tag", "host", "path"]].to_string())
