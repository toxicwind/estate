# Recovered GitHub search sort / relevance algorithm

Source-of-truth file: `ranch/github-search/legacy/rust/core/src/ranking.rs`
(`RankWeights`). Recovered 2026-10-22; this was the estate's GitHub result
sort / relevance ranking that was "lost" / parked in the legacy crate.

## The algorithm

Two weight profiles over a fixed 14-feature vector. Score for a result is the
weighted sum of per-feature signals, `normalize()` rescales the mean weight to
~1.0, and the final ordering is result score descending.

Features (vector order): `base, stars, recency, text_match, readability,
fusion, context, rarity, bm25, identifier, popularity, language_affinity,
commit_recency, ml`.

### baseline() — legacy "sum of parts"

Flat, uniform weights (everything ~1.0, fusion/context/rarity/language minor).

| base | stars | recency | text | read | fusion | context | rarity | bm25 | ident | pop | lang | commit |  ml |
| ---: | ----: | ------: | ---: | ---: | -----: | ------: | -----: | ---: | ----: | --: | ---: | -----: | --: |
|  1.0 |   1.0 |     1.0 |  1.0 |  1.0 |    0.8 |     0.8 |    0.6 |  1.0 |   1.0 | 1.0 |  0.7 |    0.9 | 1.0 |

### experimental_default() — RELEVANCE-FIRST (the tuned one)

Text match and BM25 dominate; popularity must NOT drown relevance.

| base | stars | recency | text | read | fusion | context | rarity | bm25 | ident | pop | lang | commit |  ml |
| ---: | ----: | ------: | ---: | ---: | -----: | ------: | -----: | ---: | ----: | --: | ---: | -----: | --: |
|  0.5 |   0.3 |     0.8 |  3.5 |  0.5 |    0.3 |     0.6 |    0.3 |  3.0 |   1.2 | 0.4 |  1.0 |    0.7 | 1.0 |

Key tuning rationales (from comments):

- `text_match: 3.5` + `bm25: 3.0` — a result that matches query terms beats a
  popular repo that doesn't.
- `stars: 0.3`, `popularity: 0.4` — popularity de-weighted so stars/forks can't
  drown out textual relevance.
- `rarity: 0.3` — rare query terms (specific/unique findings) have a (small)
  boost in the scorer.
- `language_affinity: 1.0` — preferred-language match matters.

## Related scorer

`legacy/rust/core/src/explainable_scorer.rs` produces a `ScoreBreakdown` per hit
(Base, Stars, Recency, TextMatch, Readability, Fusion, Context, Rarity, BM25,
Identifier, Popularity, LanguageAffinity, CommitRecency, ML) so any final score
is explainable. `DESIGN_NOTES.md` attributes the ordered-rule + score-breakdown
design to Meilisearch ranking rules and Sourcegraph's zoekt.

## Use

The recovery goal is to keep this as the canonical GitHub relevance sort.
Any future github-search must reuse `experimental_default()` (relevance-first)
unless a caller explicitly wants the legacy uniform `baseline()`.
