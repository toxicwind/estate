#!/usr/bin/env python3
"""Tests for publish_scores.py (read-only calibrated routing-score publisher).

Fixture: one probe task with known outcomes. Asserts calibration semantics
(Wilson lower-bound penalizes small samples), error-class accounting,
low-sample flagging, per-line expect override, and artifact structure —
including the read-only / scope warnings.
"""
import json
import os
import sys
import tempfile

_here = os.path.dirname(os.path.abspath(__file__))
for _cand in (_here, os.path.join(_here, "..")):
    if os.path.exists(os.path.join(_cand, "publish_scores.py")):
        sys.path.insert(0, _cand)
        break
import publish_scores as ps

EXPECT = "ABSTRACT-7X3Q"


def fixture_lines():
    L = []
    # model-a: 3/3 exact, fast
    for ms in (100, 120, 110):
        L.append({"model": "model-a", "http": 200, "lat_ms": ms,
                  "content": EXPECT})
    # model-b: 2/3 exact (one 429)
    L.append({"model": "model-b", "http": 200, "lat_ms": 100,
              "content": EXPECT})
    L.append({"model": "model-b", "http": 200, "lat_ms": 110,
              "content": EXPECT})
    L.append({"model": "model-b", "http": 429, "lat_ms": 50,
              "content": ""})
    # model-c: 0/2, all routing errors
    L.append({"model": "model-c", "http": 429, "lat_ms": 40, "content": ""})
    L.append({"model": "model-c", "http": 402, "lat_ms": 45, "content": ""})
    # model-d: 1/1 exact (low sample)
    L.append({"model": "model-d", "http": 200, "lat_ms": 100,
              "content": EXPECT})
    # model-e: 200-empty
    L.append({"model": "model-e", "http": 200, "lat_ms": 300, "content": ""})
    # model-f: per-line expect override (differs from --expect)
    L.append({"model": "model-f", "http": 200, "lat_ms": 90,
              "content": "OTHER", "expect": "OTHER"})
    return L


def test_scores():
    models, ranking = ps.score_models(fixture_lines(), EXPECT, 3)
    a, b, c, d, e, f = (models["model-" + x] for x in "abcdef")

    assert ranking[0] == "model-a", ranking  # most reliable + fast
    assert set(ranking[-2:]) == {"model-c", "model-e"}, ranking  # zero exact
    assert c["score"] == 0.0
    assert c["error_classes"] == {"http_402": 1, "http_429": 1}, c

    # Wilson lower bound is conservative: 3/3 < 1.0, and 1/1 < 3/3
    assert a["wilson95_lo"] < 1.0
    assert d["wilson95_lo"] < a["wilson95_lo"], (d, a)
    assert a["wilson95_lo"] <= a["reliability"] <= a["wilson95_hi"]

    # small samples flagged, adequately sampled not
    assert d["low_sample"] is True
    assert a["low_sample"] is False and b["low_sample"] is False

    # error classes visible separately
    assert e["error_classes"].get("empty_200") == 1, e
    assert b["error_classes"].get("http_429") == 1, b

    # latency from exact passes only
    assert a["lat_ms_p50"] == 110.0, a
    assert e["lat_ms_p50"] is None  # no exact passes -> no latency credit

    # per-line expect override counts as exact
    assert f["exact"] == 1 and f["reliability"] == 1.0, f
    print("PASS test_scores")


def test_classify():
    assert ps.classify({"http": 200, "content": EXPECT}, EXPECT) == "exact"
    assert ps.classify({"http": 200, "content": ""}, EXPECT) == "empty_200"
    assert ps.classify({"http": 200, "content": "nope"}, EXPECT) == "wrong_200"
    assert ps.classify({"http": 429, "content": ""}, EXPECT) == "http_429"
    assert ps.classify({"http": -1, "content": "boom"}, EXPECT) == "transport"
    print("PASS test_classify")


def test_artifact():
    tmp = tempfile.mkdtemp()
    inp = os.path.join(tmp, "probe.jsonl")
    with open(inp, "w") as fh:
        for r in fixture_lines():
            fh.write(json.dumps(r) + "\n")
    out = os.path.join(tmp, "scores.json")
    sys.argv = ["publish_scores.py", "--input", inp, "--expect", EXPECT,
                "--min-samples", "3", "--out", out]
    assert ps.main() == 0
    art = json.load(open(out))
    assert art["read_only"] is True
    assert "advisory only" in art["method"]
    assert "one exact-output probe task" in art["scope_warning"]
    assert art["records"] == len(fixture_lines())
    assert art["ranking"][0] == "model-a"
    # artifact carries no router config paths
    blob = json.dumps(art)
    assert "herd.yaml" not in blob
    print("PASS test_artifact")


if __name__ == "__main__":
    test_scores()
    test_classify()
    test_artifact()
    print("ALL PUBLISH TESTS PASS")
