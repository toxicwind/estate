# auto1m — virtual 1M-context composite route (prototype)

No ceiling: an automatic composite that operates over ~1M tokens using the
whole model fleet, instead of treating one model's native window as the limit.

## How it works

```
query + oversized corpus
  ├─ fits native-1M budget? ──yes──▶ direct call (DeepSeek-V4-Pro via API)
  └─ no ──▶ COMPOSITE
               ├─ query-aware chunking (sentence-aware, token-budgeted, overlap;
               │   chunks ranked by query-term overlap — most relevant maps first)
               ├─ MAP: parallel extractions via sovereign router :25104
               │   (model sovereign/free), one fact per line, [Cxxxx] tags.
               │   Fail-fast per call (120s), errors recorded, never retried.
               ├─ SCORE: batched LLM relevance scoring (ExtAgents-style),
               │   keyword fallback if scoring fails
               ├─ REDUCE: tree-collapse loop (LLMxMapReduce mr_collapse) until
               │   the fact set fits, then final answer with mandatory
               │   [Cxxxx] citations
               └─ provenance map: chunk id → source file + char span
```

## Design lineage (code-read on yote, not paper-skimmed)

- `projects/llm-mapreduce/LLMxMapReduce_V1/Generator.py` — `chunk_docs`
  (budget = window − prompt − max_tokens), `mr_map` thread-pool fan-out,
  `mr_collapse` tree loop, `mr_reduce` with chunk provenance labels.
- `projects/extagents/src/pipeline.py` — info scoring + score-sorted
  selection, exponential candidate counts, early exit.

Paper-only candidates (Parallel Context Compaction, Divide-and-Conquer
cautionary paper) were dropped: no code repos.

## Usage

```bash
# composite over a directory of docs (forces composite even if it would fit direct)
python3 auto1m.py --query "..." --corpus /path/to/docs --force-composite --out result.json
# single file
python3 auto1m.py --query "..." --corpus notes.md --out result.json
# proof test: ~700k-token real-doc corpus, 3-fact cross-chunk question
AUTO1M_MODEL=<honest-worker> python3 test_auto1m.py
# pure-function unit tests (no router needed)
python3 test_unit.py
```

## Environment

| Var | Default | Meaning |
|---|---|---|
| `AUTO1M_ROUTER` | `http://127.0.0.1:25104` | OpenAI-compatible chat endpoint (sovereign router on yote) |
| `AUTO1M_MODEL` | `sovereign/free` | map/score/reduce worker (see below) |
| `AUTO1M_DIRECT_MODEL` | `deepseek/deepseek-v4-pro-0813` | native-1M direct lane (must serve via router) |
| `AUTO1M_WORKERS` | `8` | parallel map threads |
| `AUTO1M_RETRIES` | `3` | bounded retry on transient 503/429 only |

## Worker model

Map/score/reduce calls default to `sovereign/free` (task spec: the Sovereign
Router picks the worker and fails over). Override with `AUTO1M_MODEL`, e.g.:

```bash
AUTO1M_MODEL=beellama/qwen-flash-256k python3 test_auto1m.py
```

Measured, not assumed (2026-09-21, live probes on yote through :25104):

- The free route then served a 1.2B local model whose extractions were
  unreliable (inverted facts, hallucinated endpoints, fabricated a `[C0126]`
  citation the provenance map correctly flagged as dangling).
- `deepseek/deepseek-v4-pro-0813` listed on :25104/v1/models but 503'd at
  probe time (OpenRouter 429/upstream outage wave; all :25104 chat completions
  503'd while provider circuits were open).
- The architecture is model-agnostic: proof runs name the actual serving
  worker in `test-evidence.json`. Never claim a model that doesn't serve —
  probe first (`sweep_workers.py`, `sweep_herd.py`).

`sovereign/free` stays the DEFAULT because it is the router's auto-pick lane
(Elo + health) — but the proof test names the worker that actually served.

## Proof (2026-09-21)

`test_auto1m.py` builds a ~700k-token corpus from 192 real markdown files
(`sovereign/docs`, `tau/docs`, `herd/docs`) — far beyond any single worker
model's window — and asks one question requiring facts from three different
files. Pass criteria: all key phrases present AND every `[Cxxxx]` citation
resolves to a real chunk in the provenance map. Evidence: `test-evidence.json`.

## Non-goals of this prototype

- No wiring: does not touch `sovereign-router-ts`, herd, or any live config.
- No local 1M inference: DeepSeek-V4-Pro is 1.6T MoE — the direct lane is
  API-only, never local.
- Token estimates are chars/4 (no tiktoken on yote); budgets are conservative.
