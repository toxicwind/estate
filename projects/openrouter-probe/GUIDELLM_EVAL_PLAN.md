# GuideLLM-based OpenRouter free-model eval plan

Date: 2026-09-20. Standing order: ranking runs THROUGH the GuideLLM fork
(`projects/guidellm`, upstream vllm-project/guidellm @ 4601968, remote
toxicwind/guidellm). No parallel harness.

## 1. Verdict: probe_abstract.py is KEPT (fixed), not superseded

Evidence from the fork source (verified 2026-09-20, not from docs):

- GuideLLM persists only metric aggregates to its reports (TTFT, ITL,
  end-to-end latency distributions, token counts, request success/failure).
  `GenerationResponse.text` exists in the request handler but is NOT saved
  to any report — there is no content-scoring path. It cannot score
  instruction-following.
- `probe_abstract.py` is therefore not a "parallel harness": it is the
  correctness/quality layer GuideLLM structurally lacks. Deleting it would
  lose the only quality signal in the repo.
- The script reads `OPENROUTER_API_KEY_FREE` from `/home/toxic/.secrets`
  in-process, sanitizes the key out of all error output, and never prints it.
- Verified live 2026-09-20 ~14:30 MDT through the free key: 446/446 models
  probed, 15 HTTP 200, 8 exact instruction-following matches.

## 2. Why GuideLLM needs a tokenizer (Chris asked)

Verified in `src/guidellm/data/tokenizers/huggingface.py`: the tokenizer is
used ONLY for synthetic workload shaping (building prompts of N tokens) and
token counting. It has zero effect on model quality measurement. The old
sweep used `kind=huggingface_auto,model=gpt2` for every model, which skews
token-length shaping. Fix: resolve each candidate model's REAL tokenizer
repo and pass it explicitly.

### Verified tokenizer repos (HF API, 2026-09-20)

| OpenRouter model id              | HF tokenizer repo (verified)          | tokenizer.json |
|----------------------------------|--------------------------------------|----------------|
| nex-agi/nex-n2.5-mini:free       | nex-agi/Nex-N2.5-mini                | yes            |
| nex-agi/nex-n2.5-pro:free        | nex-agi/Nex-N2.5-Pro                 | yes (family)   |
| poolside/laguna-s-2.1:free       | poolside/Laguna-S-2.1                | yes            |
| inclusionai/ling-3.0-flash-fin:free | inclusionAI/Ling-3.0-flash-Fin    | yes            |
| inclusionai/ling-3.0-flash-vl:free  | inclusionAI/Ling-3.0-flash-VL     | yes            |

### Gated on HF (401 unauthenticated — need HF_TOKEN or family fallback)

nvidia Nemotron-3 family (super-120b, ultra-550b, nano-30b, 3.5-lightning),
inclusionAI/Ling-3.0-flash-Sante, LiquidAI/LFM-2.5-2.6B,
CohereLabs north-mini-code, dots-studio/dots-3-note-preview.
Fallback order: same-family public tokenizer -> gpt2 proxy (last resort).

## 3. Two-layer eval design (composite ranking)

- Layer 1 — quality (probe_abstract.py): abstract instruction-following
  prompts, exact-match scoring. This is the RANKING input.
- Layer 2 — GuideLLM (availability/latency/throughput): synchronous profile
  over the Layer-1 passing set, per-model real tokenizers, file-data prompts.
- Composite order: abstract score -> free-on-provider -> GuideLLM p50 latency.
  Cost is NOT a factor (Chris directive).

## 4. Concrete next commands (run on yote)

KEY=$(grep -E "^[[:space:]]*(export[[:space:]]+)?OPENROUTER_API_KEY_FREE[[:space:]]*=" \
  /home/toxic/.secrets | head -1 | sed -E "s/^[^=]*=[[:space:]]*//; s/^\"//; s/\"$//")

# one model, real tokenizer, abstract prompts as file data, 10 sync requests
guidellm run \
  --backend "kind=openai_http,target=https://openrouter.ai/api/v1,model=nex-agi/nex-n2.5-mini:free,api_key=$KEY,validate_backend=False" \
  --data kind=text_file,path=/home/toxic/sovereign/projects/openrouter-probe/abstract-prompts.txt \
  --profile kind=synchronous \
  --constraint kind=max_requests,count=10 \
  --tokenizer kind=huggingface_auto,model=nex-agi/Nex-N2.5-mini \
  --output "kind=json,path=/home/toxic/sovereign/projects/openrouter-probe/guidellm/nex-n2.5-mini.json" \
  --disable-progress

Repeat per model, swapping model + tokenizer repo from the table above.
Sweep outputs land in projects/openrouter-probe/guidellm/*.json (gitignored).

## 5. Open items

- Reasoning models (nemotron-3-nano-omni-30b-a3b-reasoning, nemotron-3.5-lightning)
  wrap answers in thinking blocks -> scorer needs a thinking-strip adapter.
- Gated tokenizers need a HF token (Chris's call) or family fallback.
- Beyond instruction-following (tool use, reasoning retention, context
  behavior): future customization IN the fork (toxicwind/guidellm), not a new
  harness. The fork is currently uncustomized upstream @ 4601968.
- Tracked files probe_all.py / deep_pass.py / guidellm_sweep.sh still read
  OPENROUTER_API_KEY_1; migrate to OPENROUTER_API_KEY_FREE separately.
