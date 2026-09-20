#!/usr/bin/env python3
"""routing-score publisher: read-only calibrated routing scores from probe JSONL.

Consumes exact-output probe results (e.g. projects/openrouter-probe/*.jsonl:
{"model", "http", "lat_ms", "content"}) and emits a calibrated score
artifact. READ-ONLY by construction: it reads one input file and writes one
artifact file. It never touches herd.yaml, never parks peers, never hardcodes
model choices into router config, and never alters selection logic — the
artifact is advisory signal for humans and router-adjacent tooling only.

Calibration method (September-2026 grade, empirical not self-reported):
  - Reliability is the OBSERVED exact-output rate, never model self-reported
    confidence (Claim-Level Confidence Calibration, arXiv 2608.22483; SCOPE,
    arXiv 2602.13110).
  - Uncertainty is the Wilson 95% interval; the published reliability is the
    interval LOWER bound, so small samples are automatically penalized
    (conformal-prediction spirit, cf. A-CRC-QA arXiv 2608.12008).
  - Latency uses P50/P95 of exact passes only — a fast wrong answer scores
    nothing for speed.
  - Error classes are counted separately (http_402, http_429, empty_200,
    wrong_200, transport, ...) so correlated failure modes stay visible
    (CAGE-CAL warning, arXiv 2605.30653: agreement can mask correlated
    failures — these scores cover ONE probe task and say so in the artifact).

Composite score (transparent, components published alongside):
    score = wilson_lower_95 * 1000/(1000 + p50_ms_of_exact_passes)

Usage:
    publish_scores.py --input reverify-20260920.jsonl --expect ABSTRACT-7X3Q \\
        [--min-samples 3] [--out scores-20260920.json]
    Per-line "expect" fields override --expect when present.
"""
import argparse
import json
import math
import os
import sys
import time
from collections import Counter, defaultdict

METHOD_NOTE = (
    "empirical exact-output rate (Wilson 95% lower bound) x "
    "latency factor 1000/(1000+p50_ms); one probe task; advisory only, "
    "read-only: never writes router config"
)


def wilson(n, k, z=1.96):
    """Wilson score interval for k successes in n trials."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def pct(xs, q):
    if not xs:
        return None
    xs = sorted(xs)
    i = (len(xs) - 1) * q
    lo, hi = int(i), min(int(i) + 1, len(xs) - 1)
    return round(xs[lo] + (xs[hi] - xs[lo]) * (i - lo), 1)


def classify(rec, expect):
    http = rec.get("http")
    content = rec.get("content") or ""
    exp = rec.get("expect", expect)
    if http == 200 and content == exp:
        return "exact"
    if http != 200:
        return "transport" if http == -1 else "http_%s" % http
    return "empty_200" if not content else "wrong_200"


def score_models(records, expect, min_samples):
    by_model = defaultdict(list)
    for r in records:
        if r.get("model"):
            by_model[r["model"]].append(r)
    out = {}
    for model, rs in by_model.items():
        n = len(rs)
        classes = Counter(classify(r, expect) for r in rs)
        exact = classes.get("exact", 0)
        rel_lo, rel_hi = wilson(n, exact)
        lat = [r["lat_ms"] for r in rs
               if classify(r, expect) == "exact"
               and isinstance(r.get("lat_ms"), (int, float))]
        p50 = pct(lat, 0.5)
        speed = 1000.0 / (1000.0 + p50) if p50 is not None else 0.0
        out[model] = {
            "samples": n,
            "exact": exact,
            "reliability": round(exact / n, 4) if n else 0.0,
            "wilson95_lo": round(rel_lo, 4),
            "wilson95_hi": round(rel_hi, 4),
            "lat_ms_p50": p50,
            "lat_ms_p95": pct(lat, 0.95),
            "error_classes": dict(sorted(classes.items())),
            "low_sample": n < min_samples,
            "score": round(rel_lo * speed, 4),
        }
    ranking = sorted(out, key=lambda m: out[m]["score"], reverse=True)
    return out, ranking


def main():
    ap = argparse.ArgumentParser(description="Publish calibrated routing scores (read-only).")
    ap.add_argument("--input", required=True, help="probe results JSONL")
    ap.add_argument("--expect", default=None,
                    help="expected exact output (per-line 'expect' overrides)")
    ap.add_argument("--min-samples", type=int, default=3)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    records = []
    with open(args.input, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    if not records:
        print("no records in input", file=sys.stderr)
        return 1
    if args.expect is None and not all("expect" in r for r in records):
        print("need --expect (no per-line expect fields)", file=sys.stderr)
        return 1

    models, ranking = score_models(records, args.expect, args.min_samples)
    artifact = {
        "generated_ts": time.time(),
        "input": os.path.basename(args.input),
        "records": len(records),
        "expect": args.expect,
        "min_samples": args.min_samples,
        "method": METHOD_NOTE,
        "read_only": True,
        "scope_warning": ("one exact-output probe task; not a general quality "
                          "ranking — see RANKING.md"),
        "models": models,
        "ranking": ranking,
    }
    out_path = args.out or "scores-%d.json" % int(time.time())
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=1)
        f.write("\n")
    print("wrote %s (%d models)" % (out_path, len(models)))
    for m in ranking[:10]:
        s = models[m]
        print("  %.4f  %s  exact %d/%d  p50 %s" % (
            s["score"], m, s["exact"], s["samples"],
            s["lat_ms_p50"] if s["lat_ms_p50"] is not None else "-"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
