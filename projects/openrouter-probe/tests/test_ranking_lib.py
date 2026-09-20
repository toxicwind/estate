"""Unit tests for ranking_lib: the tokenizer-valid vs fallback tier contract.

The ranked tier is TOKENIZER-COMPARABLE models only. openrouter/free (and
any result with a fallback-labeled tokenizer_status) must NEVER appear in
the numbered ranking or the ranked results -- it belongs in fallback_tier.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ranking_lib
from ranking_lib import (
    build_report,
    is_fallback_result,
    rank_models,
    render_markdown,
    split_tiers,
)

INSTRUMENT = {"harness": "test", "ranking_rule": "quality desc"}


def mk(model, q, n=6, err=0, lat=1.0, status="ok", tok="verified",
       repo="org/model", free=True):
    return {
        "model": model,
        "status": status,
        "quality_mean": q,
        "quality_n": n,
        "n_errored": err,
        "latency_p50_s": lat,
        "ttft_p50_ms": 100.0,
        "output_tps": 20.0,
        "tokenizer_repo": repo,
        "tokenizer_status": tok,
        "free": free,
    }


def fixture_results():
    # 9 tokenizer-valid + openrouter/free on the gpt2 fallback + 1 dead
    models = [
        ("nex-agi/nex-n2.5-mini:free", 2.0, 0.8),
        ("nex-agi/nex-n2.5-pro:free", 2.0, 1.0),
        ("cohere/north-mini-code:free", 2.0, 1.2),
        ("poolside/laguna-s-2.1:free", 2.0, 1.5),
        ("nvidia/nemotron-3-super-120b-a12b:free", 2.0, 2.0),
        ("inclusionai/ling-3.0-flash-sante:free", 2.0, 2.2),
        ("nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free", 2.0, 2.5),
        ("nvidia/nemotron-3-ultra-550b-a55b:free", 2.0, 3.0),
        ("nvidia/nemotron-3.5-lightning:free", 1.8333, 1.1),
    ]
    out = [mk(m, q, lat=lat) for m, q, lat in models]
    out.append(mk("openrouter/free", 1.6667, repo="gpt2",
                  tok="fallback-labeled"))
    out.append({"model": "dead/model:free", "status": "error",
                "error": "boom", "free": True})
    return out


def test_is_fallback_result():
    assert is_fallback_result({"tokenizer_status": "fallback-labeled"})
    assert not is_fallback_result({"tokenizer_status": "verified"})
    assert not is_fallback_result({"tokenizer_status": "verified-family"})
    assert not is_fallback_result({})


def test_split_tiers_classification():
    ranked_src, fallback = split_tiers(fixture_results())
    assert len(ranked_src) == 9
    assert len(fallback) == 1
    assert fallback[0]["model"] == "openrouter/free"
    assert all(not is_fallback_result(r) for r in ranked_src)
    # dead/errored results are in neither tier
    assert all(r["model"] != "dead/model:free" for r in ranked_src + fallback)


def test_rank_models_ordering():
    ranked_src, _ = split_tiers(fixture_results())
    ranked = rank_models(ranked_src)
    assert ranked[0]["model"] == "nex-agi/nex-n2.5-mini:free"  # fastest of the 2.0s
    assert ranked[-1]["model"] == "nvidia/nemotron-3.5-lightning:free"  # 1.8333 last
    qualities = [r["quality_mean"] for r in ranked]
    assert qualities == sorted(qualities, reverse=True)


def test_build_report_nine_ranked_plus_fallback():
    report = build_report("ts", INSTRUMENT, fixture_results())
    assert len(report["ranking"]) == 9
    assert len(report["fallback_tier"]) == 1
    assert report["fallback_tier"][0]["model"] == "openrouter/free"
    # results carries the ranked tier only (9); fallback lives in
    # fallback_tier, dead in dead_or_errored
    assert len(report["results"]) == 9
    assert all(r["model"] != "openrouter/free" for r in report["results"])
    assert len(report["dead_or_errored"]) == 1


def test_openrouter_free_absent_from_ranking_and_ranked_results():
    report = build_report("ts", INSTRUMENT, fixture_results())
    assert "openrouter/free" not in report["ranking"]
    ranked_models = set(report["ranking"])
    ranked_results = [r for r in report["results"]
                      if r["model"] in ranked_models]
    assert len(ranked_results) == 9
    assert all(r["model"] != "openrouter/free" for r in ranked_results)


def test_fallback_tier_entry_complete():
    report = build_report("ts", INSTRUMENT, fixture_results())
    fb = report["fallback_tier"][0]
    assert fb["model"] == "openrouter/free"
    assert fb["tokenizer_repo"] == "gpt2"
    assert "gpt2" in fb["note"] and "NOT comparable" in fb["note"]
    assert fb["result"]["model"] == "openrouter/free"
    assert fb["result"]["quality_mean"] == 1.6667


def test_render_markdown_fallback_section():
    report = build_report("ts", INSTRUMENT, fixture_results())
    ranked = rank_models(split_tiers(fixture_results())[0])
    fallback = split_tiers(fixture_results())[1]
    md = render_markdown(
        title="# Eval ranking ts",
        header_lines=["Instrument: test."],
        ranked=ranked,
        fallback=fallback,
        dead_or_errored=report["dead_or_errored"],
    )
    # numbered ranked rows: exactly 9
    ranked_rows = [l for l in md.split("\n")
                   if l.startswith("| ") and l[2].isdigit()]
    assert len(ranked_rows) == 9
    assert "openrouter/free" not in "\n".join(ranked_rows)
    # fallback section present with a complete data row
    assert "## Fallback tier — NOT ranked" in md
    fb_rows = [l for l in md.split("\n") if "openrouter/free" in l]
    assert len(fb_rows) == 1
    cells = [c.strip() for c in fb_rows[0].split("|")]
    # | model | quality mean | n | err | lat p50 | ttft p50 | out tok/s | tokenizer |
    assert cells[1] == "openrouter/free"
    assert cells[2] == "1.67"
    assert cells[8] == "gpt2 (fallback)"


def test_report_json_serializable_and_idempotent():
    results = fixture_results()
    r1 = build_report("ts", INSTRUMENT, results)
    r2 = build_report("ts", INSTRUMENT, fixture_results())
    s1 = json.dumps(r1, sort_keys=True)
    s2 = json.dumps(r2, sort_keys=True)
    assert s1 == s2  # idempotent across runs
    # ranking names match results 1:1 and in order
    assert [r["model"] for r in r1["results"]] == r1["ranking"]
