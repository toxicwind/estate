#!/usr/bin/env python3
"""Columnar analytics over parquet: describe, ingest, log, group, fit, anomaly.

Pure pyarrow + pandas + numpy so it runs in the existing sovereign venv with
no new dependencies. Every subcommand writes parquet back out, so analyses
compose instead of ending in a terminal table.

    pq.py describe  FILE.parquet
    pq.py ingest    events.jsonl -o events.parquet
    pq.py log       bili.log -o bili.parquet --grep 'local='
    pq.py group     FILE.parquet --by kind --agg count,bytes:sum,bytes:max
    pq.py fit       FILE.parquet --target ms --features msgs,inbound_bytes
    pq.py anomaly   FILE.parquet --col ms --method mad
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

LOG_HEAD = re.compile(r"^(?P<ts>\S+)\s+\[(?P<level>\w+)\]\s+\[(?P<tag>[^\]]+)\]\s+(?P<msg>.*)$")
UNITS = {"b": 1, "kb": 1000, "mb": 1000**2, "kib": 1024, "mib": 1024**2}
AGGS = {"count": "count", "sum": "sum", "mean": "mean", "min": "min",
        "max": "max", "nunique": "nunique", "std": "std"}


# ---------------------------------------------------------------- loading


def load(path: str) -> pd.DataFrame:
    """Read a parquet file, or a .jsonl / .json / .csv sidecar."""
    p = Path(path)
    if p.suffix == ".parquet":
        return pq.read_table(p).to_pandas()
    if p.suffix in (".jsonl", ".ndjson"):
        return pd.read_json(p, lines=True)
    if p.suffix == ".json":
        return pd.DataFrame(json.loads(p.read_text()))
    if p.suffix == ".csv":
        return pd.read_csv(p)
    raise SystemExit(f"pq: unsupported input {p.suffix!r} (want .parquet/.jsonl/.json/.csv)")


def numeric_cols(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]


def write(df: pd.DataFrame, out: str) -> None:
    pq.write_table(pa.Table.from_pandas(df, preserve_index=False), out)
    print(f"wrote {len(df):,} rows x {len(df.columns)} cols -> {out}", file=sys.stderr)


# ---------------------------------------------------------------- log


def parse_log(path: str) -> pd.DataFrame:
    """Parse `TS [level] [tag] message` logs and lift common fields to columns.

    These service logs are already close to tabular: timings, byte counts and
    model names appear as `key=value` or with a unit suffix. Extracting them
    once at ingest keeps every later query numeric.
    """
    rows = []
    for line in Path(path).read_text(encoding="utf8", errors="replace").splitlines():
        m = LOG_HEAD.match(line)
        if not m:
            continue
        d = m.groupdict()
        msg = d["msg"]
        row: dict = {"ts": d["ts"], "level": d["level"], "tag": d["tag"], "msg": msg}
        v = re.search(r"local=(\d+)ms", msg)
        if v:
            row["local_ms"] = float(v.group(1))
        v = re.search(r"(\d+)ms\b", msg)
        if v:
            row["ms"] = float(v.group(1))
        v = re.search(r":\s*(\d+)\s+msgs", msg)
        if v:
            row["msgs"] = float(v.group(1))
        v = re.search(r"usage=(\d+)%", msg)
        if v:
            row["usage_pct"] = float(v.group(1))
        v = re.search(r"model=([^\s,]+)", msg)
        if v:
            row["model"] = v.group(1)
        v = re.search(r"\((\d+)/(\d+)\)", msg)
        if v:
            row["used"] = float(v.group(1))
            row["window"] = float(v.group(2))
        for key in ("inbound", "outbound"):
            v = re.search(rf"{key}=([\d.]+)\s*(B|KiB|MiB|KB|MB)", msg, re.I)
            if v:
                row[f"{key}_bytes"] = float(v.group(1)) * UNITS[v.group(2).lower()]
        rows.append(row)
    df = pd.DataFrame(rows)
    if "ts" in df.columns:
        df["ts"] = pd.to_datetime(df["ts"], errors="coerce", format="mixed", utc=True)
    return df


def cmd_log(args: argparse.Namespace) -> int:
    df = parse_log(args.file)
    if args.grep:
        df = df[df["msg"].str.contains(args.grep, case=False, na=False)]
    print(f"{args.file}: {len(df):,} parsed log lines", file=sys.stderr)
    write(df, args.out)
    return 0


# ---------------------------------------------------------------- describe


def cmd_describe(args: argparse.Namespace) -> int:
    df = load(args.file)
    print(f"{args.file}: {len(df):,} rows x {len(df.columns)} cols")
    if args.file.endswith(".parquet"):
        meta = pq.ParquetFile(args.file).metadata
        print(f"row groups: {meta.num_row_groups}  created by: {meta.created_by}")
    out = []
    for c in df.columns:
        s = df[c]
        miss = int(s.isna().sum())
        row: dict = {
            "column": c,
            "dtype": str(s.dtype),
            "nulls": miss,
            "nulls_pct": round(100 * miss / len(df), 2) if len(df) else 0.0,
            "unique": int(s.nunique(dropna=True)),
        }
        if pd.api.types.is_numeric_dtype(s):
            v = s.dropna()
            if len(v):
                row |= {
                    "min": float(v.min()),
                    "mean": round(float(v.mean()), 4),
                    "std": round(float(v.std()), 4) if len(v) > 1 else 0.0,
                    "p50": float(v.quantile(0.50)),
                    "p95": float(v.quantile(0.95)),
                    "max": float(v.max()),
                }
        else:
            top = s.value_counts().head(3)
            row["top"] = ", ".join(f"{k!r}:{v}" for k, v in top.items())[:80]
        out.append(row)
    d = pd.DataFrame(out).set_index("column")
    with pd.option_context("display.width", 220, "display.max_columns", 50):
        print(d.to_string())
    if args.out:
        d.reset_index().to_parquet(args.out, index=False)
        print(f"profile -> {args.out}", file=sys.stderr)
    return 0


# ---------------------------------------------------------------- ingest


def cmd_ingest(args: argparse.Namespace) -> int:
    """Turn a JSONL or CSV stream into typed parquet."""
    df = load(args.file)
    for c in df.columns:
        if any(t in c.lower() for t in ("time", "ts", "_at", "date")) and df[c].dtype == object:
            parsed = pd.to_datetime(df[c], errors="coerce", format="mixed", utc=True)
            if parsed.notna().mean() > 0.5:
                df[c] = parsed
    for c in numeric_cols(df):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    write(df.dropna(how="all"), args.out)
    return 0


# ---------------------------------------------------------------- group


def cmd_group(args: argparse.Namespace) -> int:
    """Group by one or more keys, applying count/sum/mean/min/max per column."""
    df = load(args.file)
    by = [b.strip() for b in args.by.split(",")]
    bad = [b for b in by if b not in df.columns]
    if bad:
        raise SystemExit(f"pq: no such column(s): {', '.join(bad)}")

    aggs: dict[str, list[str]] = {}
    # Accept BOTH forms: `--agg a --agg b` and `--agg a,b`. The help said
    # "repeatable", so the comma form silently produced one malformed spec and a
    # confusing "bad agg function" error that named the whole joined string.
    specs = [s.strip() for raw in (args.agg or []) for s in raw.split(",") if s.strip()]
    for spec in specs:
        if ":" in spec:
            col, fn = spec.split(":", 1)
            if fn not in AGGS:
                raise SystemExit(f"pq: bad agg function {fn!r} (want {'/'.join(AGGS)})")
            if col not in df.columns:
                raise SystemExit(f"pq: no such column: {col}")
            aggs.setdefault(col, []).append(AGGS[fn])
        elif spec in AGGS:
            aggs.setdefault("__rows__", []).append(AGGS[spec])
        else:
            if spec not in df.columns:
                raise SystemExit(f"pq: no such column: {spec}")
            aggs.setdefault(spec, []).append("count")

    if "__rows__" in aggs:
        df = df.assign(__rows__=1)
    if aggs:
        g = df.groupby(by, dropna=False).agg(aggs)
    else:
        g = df.groupby(by, dropna=False).size().to_frame("count")
    g = g.sort_values(by[0]).reset_index()
    with pd.option_context("display.width", 220, "display.max_columns", 60):
        print(g.head(args.limit).to_string(index=False))
    print(f"\n{len(g):,} groups", file=sys.stderr)
    if args.out:
        write(g, args.out)
    return 0


# ---------------------------------------------------------------- fit


def cmd_fit(args: argparse.Namespace) -> int:
    """Ordinary least squares with an intercept, plus fit diagnostics.

    Coefficients come from a least-squares solve, not a matrix inverse, so
    collinear predictors degrade to a low rank instead of a wall of NaN. VIF
    names which feature is responsible.
    """
    df = load(args.file)
    feats = [f.strip() for f in (args.features or "").split(",") if f.strip()]
    if not feats:
        feats = [c for c in numeric_cols(df) if c != args.target]
    if args.target not in df.columns:
        raise SystemExit(f"pq: no such target column: {args.target}")
    bad = [f for f in feats if f not in df.columns]
    if bad:
        raise SystemExit(f"pq: no such feature column(s): {', '.join(bad)}")

    work = df[[args.target, *feats]].apply(pd.to_numeric, errors="coerce").dropna()
    n = len(work)
    if n < len(feats) + 2:
        raise SystemExit(f"pq: need more than {len(feats) + 1} complete rows, have {n}")

    y = work[args.target].to_numpy(float)
    X = work[feats].to_numpy(float)
    X1 = np.column_stack([np.ones(n), X])
    beta = np.linalg.lstsq(X1, y, rcond=None)[0]
    resid = y - X1 @ beta
    ss_res = float(resid @ resid)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    dof = n - len(feats) - 1
    adj = 1 - (1 - r2) * (n - 1) / dof if dof > 0 else float("nan")
    s2 = ss_res / dof
    rmse = float(np.sqrt(ss_res / n))

    vif: dict[str, float] = {}
    for i, f in enumerate(feats):
        others = np.delete(np.arange(len(feats)), i)
        if others.size == 0:
            vif[f] = 1.0
            continue
        Z = np.column_stack([np.ones(n), X[:, others]])
        b = np.linalg.lstsq(Z, X[:, i], rcond=None)[0]
        r = X[:, i] - Z @ b
        sst = float(((X[:, i] - X[:, i].mean()) ** 2).sum())
        r2i = 1 - float(r @ r) / sst if sst > 0 else 0.0
        vif[f] = float("inf") if r2i >= 1 - 1e-12 else 1 / (1 - r2i)

    se = np.sqrt(s2 * np.diag(np.linalg.pinv(X1.T @ X1)))
    pvals = []
    for b, s in zip(beta, se):
        t = abs(b / s) if s > 0 else float("nan")
        pvals.append(float("nan") if not np.isfinite(t) else _two_sided_t(t, dof))

    print(f"n={n:,}  features={len(feats)}  dof={dof}")
    print(f"R2={r2:.4f}  adjR2={adj:.4f}  RMSE={rmse:.4f}  sigma={np.sqrt(s2):.4f}")
    print(f"\n{'term':<24}{'coef':>14}{'p':>12}{'VIF':>10}")
    print(f"{'(intercept)':<24}{beta[0]:>14.5f}{'-':>12}{'-':>10}")
    for f, b, p in zip(feats, beta[1:], pvals[1:]):
        print(f"{f:<24}{b:>14.5f}{p:>12.4g}{vif[f]:>10.2f}"
              f"{'  <-- collinear' if vif[f] > 10 else ''}")

    if args.out:
        rows = [{"term": "(intercept)", "coef": float(beta[0]), "p": None, "vif": None}]
        rows += [{"term": f, "coef": float(b),
                  "p": None if not np.isfinite(p) else p, "vif": vif[f]}
                 for f, b, p in zip(feats, beta[1:], pvals[1:])]
        write(pd.DataFrame(rows), args.out)
        diag = {"n": n, "r2": r2, "adj_r2": float(adj), "rmse": rmse, "sigma": float(np.sqrt(s2))}
        Path(args.out).with_suffix(".json").write_text(json.dumps(diag, indent=2))
    return 0


def _two_sided_t(t: float, dof: int) -> float:
    """Two-sided p-value for Student's t, without pulling in scipy.

    Uses the regularised incomplete beta I_x(dof/2, 1/2) evaluated by the
    Lentz continued fraction, normalised by the complete beta from lgamma.
    """
    if dof <= 0 or not np.isfinite(t):
        return float("nan")
    x = dof / (dof + t * t)
    a, b, floor = dof / 2.0, 0.5, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < floor:
        d = floor
    d = 1.0 / d
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < floor:
            d = floor
        c = 1.0 + aa / c
        if abs(c) < floor:
            c = floor
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < floor:
            d = floor
        c = 1.0 + aa / c
        if abs(c) < floor:
            c = floor
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 3e-16:
            break
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                  + a * math.log(x) + b * math.log1p(-x))
    return min(1.0, max(0.0, bt * h / a))


# ---------------------------------------------------------------- anomaly


def cmd_anomaly(args: argparse.Namespace) -> int:
    """Flag outliers by robust z-score (MAD) or by IQR fence.

    MAD is the default because one 10x outlier in a latency series makes a
    mean/stdev rule flag the entire healthy population.
    """
    df = load(args.file)
    cols = [c.strip() for c in args.col.split(",")] if args.col else numeric_cols(df)
    bad = [c for c in cols if c not in df.columns]
    if bad:
        raise SystemExit(f"pq: no such column(s): {', '.join(bad)}")

    frames = []
    for c in cols:
        v = pd.to_numeric(df[c], errors="coerce")
        med = v.median()
        if args.method == "iqr":
            q1, q3 = v.quantile(0.25), v.quantile(0.75)
            iqr = q3 - q1
            scale = iqr if iqr else np.nan
        else:
            scale = 1.4826 * float((v - med).abs().median())
        score = (v - med) / (scale if scale else np.nan)
        out = pd.DataFrame({
            "row": np.arange(len(df)),
            "column": c,
            "value": v.to_numpy(),
            "score": score.to_numpy(),
            "is_outlier": (score.abs() > args.threshold).fillna(False).to_numpy(),
        })
        frames.append(out)
        n_out = int(out["is_outlier"].sum())
        print(f"{c:<24} outliers {n_out:>6,} / {len(df):>8,} "
              f"({100 * n_out / max(len(df), 1):.2f}%)  median={med:.4g}  thresh=+/-{args.threshold}")
        if 0 < n_out <= 15:
            for _, r in out[out["is_outlier"]].head(15).iterrows():
                print(f"    row {int(r['row']):>8}  {c}={r['value']:.6g}  score={r['score']:.2f}")

    if args.out:
        write(pd.concat(frames, ignore_index=True), args.out)
    return 0


# ---------------------------------------------------------------- cli


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="pq.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    lg = sub.add_parser("log", help="parse a TS [level] [tag] msg log into parquet")
    lg.add_argument("file")
    lg.add_argument("--grep", help="keep only lines matching this substring")
    lg.add_argument("-o", "--out", required=True)
    lg.set_defaults(fn=cmd_log)

    d = sub.add_parser("describe", help="schema and per-column profile")
    d.add_argument("file")
    d.add_argument("-o", "--out", help="write the profile as parquet")
    d.set_defaults(fn=cmd_describe)

    g = sub.add_parser("ingest", help="jsonl/json/csv -> typed parquet")
    g.add_argument("file")
    g.add_argument("-o", "--out", required=True)
    g.set_defaults(fn=cmd_ingest)

    r = sub.add_parser("group", help="group by keys and aggregate")
    r.add_argument("file")
    r.add_argument("--by", required=True, help="comma separated key columns")
    r.add_argument("--agg", action="append", help="col:count|sum|mean|min|max|nunique|std; comma separated or repeated; a bare agg name counts rows, a bare column name counts it")
    r.add_argument("--limit", type=int, default=50)
    r.add_argument("-o", "--out")
    r.set_defaults(fn=cmd_group)

    f = sub.add_parser("fit", help="OLS regression with R2, p-values and VIF")
    f.add_argument("file")
    f.add_argument("--target", required=True)
    f.add_argument("--features", help="comma separated; defaults to every other numeric column")
    f.add_argument("-o", "--out")
    f.set_defaults(fn=cmd_fit)

    a = sub.add_parser("anomaly", help="outlier detection on numeric columns")
    a.add_argument("file")
    a.add_argument("--col", help="comma separated; defaults to all numeric columns")
    a.add_argument("--method", choices=("mad", "iqr"), default="mad")
    a.add_argument("--threshold", type=float, default=3.5)
    a.add_argument("-o", "--out")
    a.set_defaults(fn=cmd_anomaly)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
