# Upstream audit — toxicwind/guidellm fork vs vllm-project/guidellm

- **Date:** 2026-09-20 ~15:35 MDT
- **Auditor:** durable-integration (ember, subagent)
- **Scope:** our fork `toxicwind/guidellm` against upstream `vllm-project/guidellm`.
- **Fork HEAD:** `6b40c21e251a5095a7ae8064a6603a3f2c4b6d32`
- **Upstream HEAD:** `4601968d8a06ffc1aecce987753da1118ea637a0`
- **Status:** AUDIT ONLY — no PRs opened, no branches moved, fork history untouched.

## TL;DR

Our fork carries **4 commits** on top of upstream, all benchmark-quality improvements
built for our herd benchmarking (2026-09-20). All four are cleanly separable and
**upstreamable in principle** — but no PRs are opened by this audit. Opening PRs to
an external repo is an outward-facing action and Chris's call. The fork's history is
intact (no squashes, no rewrites); the delta is documented here so the upstream
decision can be made with full context.

## The delta (our commits, oldest first)

### 1. `74ec8623` — Pluggable response-quality scoring for benchmarks
New `guidellm/benchmark/scoring/` package: scorer protocol + registry with a built-in
`instruction_following` scorer (exact/contains semantics). Touches
`benchmarker.py`, `entrypoints.py`, `schemas/{accumulator,base,benchmark}.py`.
**Upstreamable:** yes — self-contained feature, additive, no behavior change to
existing paths. Would need upstream's test/style conventions checked.

### 2. `bb96157f` — Classify HuggingFace tokenizer load failures into actionable errors
`data/tokenizers/huggingface.py` (+142-line test): distinguishes auth failures,
missing revisions, network errors instead of one opaque exception.
**Upstreamable:** yes — pure error-taxonomy improvement, additive, tested.

### 3. `99540b90` — scoring: empty output scores 0.0, exception zeros aggregate + error metadata
`_score_request` no longer early-returns on empty/missing output; scorer exceptions
record 0.0 with error metadata; `score_details` persisted; true nested
thinking-strip. Touches `accumulator.py`, `adapters.py`, `request_stats.py`, tests.
**Upstreamable:** yes, with discussion — changes scoring semantics (empty output is a
measurement, not a skip). Upstream may have opinions; the commit message documents
the rationale.

### 4. `6b40c21e` — scoring: quality aggregates cover completed requests only
Follow-up to #3: per-request scores recorded for every terminal request, but
aggregates cover completed requests only. Touches `accumulator.py`, tests.
**Upstreamable:** yes, as a pair with #3.

## Why not upstreamed now

1. **Outward action.** PRs to `vllm-project/guidellm` speak as Chris/toxicwind to an
   external project. That is Chris's decision, not an agent's.
2. **Harness-specific tuning.** Commits #3–#4 encode our judgment about what counts
   as a measurement vs a skip in *our* benchmark runs. Reasonable people (and
   upstream maintainers) may disagree; a PR needs that debate, not a drive-by.
3. **No urgency.** The fork serves our benchmarks today; upstream gains nothing
   until the PRs exist, and nothing is lost by waiting for Chris's call.

## History preservation

- Fork history is **intact**: 4 commits, full messages, no squashes, no rewrites,
  no force-pushes. `git log 4601968d..6b40c21e` reproduces the delta above.
- If Chris approves upstreaming: open one PR per commit (or per logical pair
  #3+#4) from a branch cut at the fork HEAD — never rewrite the fork's main.
- If upstream accepts: merge upstream back into the fork (merge commit, no rebase
  of our history) so the fork's histogram stays honest.

## Deep links

- Master README: `/home/toxic/sovereign/README.md`
- Our fork: https://github.com/toxicwind/guidellm
- Upstream: https://github.com/vllm-project/guidellm
- Local working copy (git-ignored, benchmark runs): `/home/toxic/sovereign/projects/guidellm/`
- Permanent tooling from today's work: `/home/toxic/sovereign/skills/surgical-edit/`
