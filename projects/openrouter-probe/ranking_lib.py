"""Shared ranking/report logic for the openrouter-probe eval stack.

Single source of truth for the quality-first ranking semantics, used by
both eval_runner.py (live runs) and merge_ranking.py (reconstruction of
crashed runs). The ranked tier is TOKENIZER-COMPARABLE models only;
results whose tokenizer_status is a fallback label (e.g. openrouter/free
on the explicitly labelled gpt2 fallback) go to fallback_tier and NEVER
enter the numbered ranking.
"""
from __future__ import annotations

FALLBACK_TOKENIZER_STATUSES = ("fallback-labeled",)

FALLBACK_NOTE = (
    "No stable tokenizer; ran on the explicitly labelled gpt2 fallback. "
    "Token counts and tokenizer-derived metrics are NOT comparable with "
    "the ranked tier. Deterministic quality score reported for the record."
)


def is_fallback_result(r: dict) -> bool:
    """True when a result ran on a labeled fallback tokenizer."""
    return r.get("tokenizer_status") in FALLBACK_TOKENIZER_STATUSES


def split_tiers(results: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split successful results into (ranked_candidates, fallback).

    Only status == "ok" results with a quality mean participate at all;
    dead/errored entries are excluded from both tiers (they surface in
    dead_or_errored).
    """
    ok = [
        r
        for r in results
        if r.get("status") == "ok" and r.get("quality_mean") is not None
    ]
    ranked_src = [r for r in ok if not is_fallback_result(r)]
    fallback = [r for r in ok if is_fallback_result(r)]
    return ranked_src, fallback


def rank_key(r: dict):
    """Quality desc, provider-free desc, latency p50 asc."""
    return (
        -r["quality_mean"],
        -(1 if r.get("free") else 0),
        r["latency_p50_s"] if r["latency_p50_s"] is not None else float("inf"),
    )


def rank_models(candidates: list[dict]) -> list[dict]:
    """Order ranked-tier candidates best-first."""
    return sorted(candidates, key=rank_key)


def build_report(ts: str, instrument: dict, results: list[dict]) -> dict:
    """Aggregate JSON: ranking (tokenizer-valid only) + fallback_tier."""
    ranked_src, fallback = split_tiers(results)
    ranked = rank_models(ranked_src)
    return {
        "ts": ts,
        "instrument": instrument,
        "ranking": [r["model"] for r in ranked],
        "results": results,
        "fallback_tier": [
            {
                "model": r["model"],
                "tokenizer_repo": r.get("tokenizer_repo", "gpt2"),
                "note": FALLBACK_NOTE,
                "result": r,
            }
            for r in fallback
        ],
        "dead_or_errored": [r for r in results if r.get("status") != "ok"],
    }


def _fmt_lat(r: dict) -> str:
    return f"{r['latency_p50_s']:.2f}" if r["latency_p50_s"] is not None else "?"


def _fmt_tt(r: dict) -> str:
    return f"{r['ttft_p50_ms']:.0f}" if r.get("ttft_p50_ms") else "?"


def _fmt_tps(r: dict) -> str:
    return f"{r['output_tps']:.1f}" if r.get("output_tps") else "?"


def ranked_table_rows(ranked: list[dict]) -> list[str]:
    rows = []
    for i, r in enumerate(ranked, 1):
        rows.append(
            f"| {i} | {r['model']} | {r['quality_mean']:.2f} | "
            f"{int(r['quality_n'] or 0)} | {r['n_errored']} | "
            f"{_fmt_lat(r)} | {_fmt_tt(r)} | {_fmt_tps(r)} | "
            f"{r['tokenizer_repo']} |"
        )
    return rows


def fallback_table_rows(fallback: list[dict]) -> list[str]:
    rows = []
    for r in fallback:
        rows.append(
            f"| {r['model']} | {r['quality_mean']:.2f} | "
            f"{int(r['quality_n'] or 0)} | {r['n_errored']} | "
            f"{_fmt_lat(r)} | {_fmt_tt(r)} | {_fmt_tps(r)} | "
            f"gpt2 (fallback) |"
        )
    return rows


RANKED_TABLE_HEADER = [
    "| rank | model | quality mean | n | err | lat p50 (s) | ttft p50 (ms) | out tok/s | tokenizer |",
    "|---|---|---|---|---|---|---|---|---|",
]

FALLBACK_TABLE_HEADER = [
    "| model | quality mean | n | err | lat p50 (s) | ttft p50 (ms) | out tok/s | tokenizer |",
    "|---|---|---|---|---|---|---|---|",
]


def render_markdown(
    title: str,
    header_lines: list[str],
    ranked: list[dict],
    fallback: list[dict],
    dead_or_errored: list[dict],
    dead_lines: list[str] | None = None,
    notes: list[str] | None = None,
) -> str:
    """Full Markdown report: ranked table, fallback tier, dead list, notes."""
    md = [title, "", *header_lines, "", *RANKED_TABLE_HEADER]
    md += ranked_table_rows(ranked)
    if fallback:
        md += [
            "",
            "## Fallback tier — NOT ranked (no stable tokenizer)",
            "",
            "These models ran on the explicitly labelled gpt2 fallback and are "
            "NOT tokenizer-comparable with the ranked tier. Deterministic quality "
            "scores reported for the record only.",
            "",
            *FALLBACK_TABLE_HEADER,
        ]
        md += fallback_table_rows(fallback)
    if dead_or_errored:
        md += ["", "## Dead or errored"]
        md += dead_lines if dead_lines else [r["model"] for r in dead_or_errored]
    if notes:
        md += ["", "## Notes", *[f"- {n}" for n in notes]]
    return "\n".join(md) + "\n"
