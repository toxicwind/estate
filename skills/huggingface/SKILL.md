---
name: huggingface
description: >
  Hugging Face Hub: model search, repo inspection, tokenizer sourcing. Verify repos contain what is needed and understand gating and auth. Triggers on: Hugging Face, model search, tokenizer.
---

# Hugging Face Hub — model search, repo inspection, tokenizer sourcing

Find real Hugging Face repos, verify they contain what you need (tokenizer
files, weights, config), and understand gating/auth. Built 2026-09-20 after a
bench run failed on phantom tokenizer repos that were never checked live.

## The one rule

**Repo IDs are claims until the Hub API confirms them.** A name that looks
right (`nvidia/NVIDIA-Nemotron-3-*-NVFP4`, `LGAI-EXAONE/EXAONE-4.0-1.2B`) is not
evidence. `GET https://huggingface.co/api/models/<id>` returning 200 with a
`siblings` list is evidence. Never mark a repo verified from a model card,
a forum post, or memory — check it live, today.

## Fast repo check (no auth needed for public repos)

```bash
curl -s -m 20 "https://huggingface.co/api/models/<org>/<name>" | python3 -c "
import json,sys
d = json.load(sys.stdin)
sibs = [s['rfilename'] for s in d.get('siblings', [])]
tok = [s for s in sibs if 'token' in s.lower()]
print('gated:', d.get('gated'), '| files:', len(sibs))
print('tokenizer files:', tok if tok else 'NONE')"
```

Interpretation:
- **200 + siblings** → repo exists. `gated: false` → fully public.
- **307 Temporary Redirect** → the ID exists but your **casing is wrong**.
  The redirect target shows the canonical case (e.g. `nex-agi/Nex-N2.5-mini`,
  not `nex-agi/Nex-n2.5-mini`). `curl -L` follows it, but downstream tools
  (huggingface_hub, GuideLLM) may not — store the canonical case.
- **401 "Invalid username or password"** → the repo is **gated** (license
  acceptance required). It exists, but files are invisible without an
  authorized token. Do not treat as "missing".
- **404** → genuinely absent (or renamed/pulled). Search for the successor.

## Search

```
GET https://huggingface.co/api/models?search=<query>&limit=20
```

- Search is fuzzy and ranks by popularity; verify the exact ID from results.
- Filter in code on `gated` — prefer ungated repos for automation.
- Generation families move: a NIM model named `ministral-8b-2512` may map to
  a repo named `mistralai/Ministral-3-8B-Instruct-2512` (note the `-3-`).
  Search `ministral` and read the IDs; don't construct them.

## Tokenizer sourcing (for benchmarks like GuideLLM)

1. List `siblings`, filter filenames containing `token`.
2. You want `tokenizer.json` (fast, preferred) or `tokenizer.model`
   (SentencePiece — needs the `sentencepiece` package) plus
   `tokenizer_config.json`.
3. **Quant repos share the base tokenizer** — but verify, don't assume: check
   that `tokenizer.json` exists in the quant repo itself
   (e.g. `nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-NVFP4` ships its own copy).
4. GGUF repos (bartowski, ggml-org, unsloth) usually bundle `tokenizer.json`
   — a valid fallback when the canonical repo is gated.
5. If the canonical repo is gated and no ungated mirror exists, the honest
   answer is "no verified tokenizer", not a family guess. A same-family
   tokenizer (e.g. Mistral NeMo's Tekken for a Mistral-Nemo NIM) is a
   **provisional** pick: mark it as such, never as verified.

## Auth for gated repos

- `Authorization: Bearer <HF_TOKEN>` on the API or `huggingface-cli login`.
- Gated repos also need **license acceptance on the account** — a valid token
  alone is not enough. If the token is expired you'll get an explicit
  "token is expired" error; treat stored tokens as perishable and re-check.
- Never print token values. Liveness verdicts only.

## Gotchas (all observed live)

- Model cards (build.nvidia.com `<id>.md`) sometimes name HF repos that have
  since been renamed or gated — the card is a lead, the API is the verdict.
- `private: true` repos 404 for anonymous callers — indistinguishable from
  absent without auth.
- Rate limits are generous for anonymous reads; no key needed for public
  metadata. If you get 429s, you're doing something wrong (tight loop) —
  back off, don't hammer.
- `resolve` URLs: `https://huggingface.co/<id>/resolve/main/tokenizer.json`
  downloads the file directly; `HEAD` it to confirm existence cheaply.