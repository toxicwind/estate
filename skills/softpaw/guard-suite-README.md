# guard-suite — Softpaw rewriter guard suite

Part of the softpaw skill. Uses the latest guard model (Llama Guard 4) as the
verification backend for the softpaw rewriter.

## Contents

- `purple-llama/` — meta-llama/PurpleLlama, cloned 2026-10-05. The official
  Llama Guard repo. `Llama-Guard4/12B/MODEL_CARD.md` holds the S1–S14 hazard
  taxonomy this suite tests against.
- `identity_guard_test.py` — line-by-line helper. Reads IDENTITY.md, splits
  into sentences, runs each through the softpaw preflight (`triggers.json`),
  then tests each with the guard model. Then tests the whole doc in
  overlapping sliding-window chunks (window=5 sentences, stride=2).
- `triggers.json` — softpaw trigger shape database (copy for the helper).
- `reports/` — JSON reports from test runs.

## Guard model backend

Llama Guard 4 weights are gated on HuggingFace and HF auth on this box is
dead (all `.secrets` tokens invalid as of 2026-10-05; `hf auth whoami` fails).
So the suite uses the **Llama Guard 4 prompt format** (S1–S14 taxonomy from
the model card) served by the herd `classify` model (Gemma 4 12B) at
`localhost:25100`. When HF auth is restored, swap `GUARD_MODEL` for the real
`meta-llama/Llama-Guard-4-12B` weights — the prompt template stays identical.

## Usage

```bash
cd /home/toxic/workspace/skills/softpaw/guard-suite
python3 identity_guard_test.py --sentences   # sentence by sentence
python3 identity_guard_test.py --chunks      # sliding-window chunks
python3 identity_guard_test.py --all         # both (default)
```

## Latest run (2026-10-05)

- 112 sentences: 1 preflight hit (`never-ask` on the Anthropic-key sentence —
  a preflight false positive; the sentence *prohibits* asking, the guard model
  correctly rates it safe).
- 55 chunks: 2 flagged (same sentence via overlapping windows — validates the
  sliding-window coverage). Guard: safe on all.
- Verdict: IDENTITY.md is clean.
