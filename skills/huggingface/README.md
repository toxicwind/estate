# huggingface

Hugging Face Hub: model search, repo inspection, tokenizer sourcing. Verify repos contain what is needed and understand gating and auth. Triggers on: Hugging Face, model search, tokenizer.

&larr; **Back to top** <!-- for-the-badge alignment -->

## Hero

Resolves Hugging Face repo IDs from names that may look right but aren't evidence, verifies repos live via the Hub API, and surfaces tokenizer files and gating status. Prevents phantom tokenizer repos from breaking benchmarks — every claim is checked live against `huggingface.co/api/models/<id>`.

## What It Does

- **Live repo verification**: `curl -s -m 20 "https://huggingface.co/api/models/<org>/<name>"` returns 200 with siblings list, 307 for wrong casing, 401 for gated, 404 for truly absent
- **Casing correction**: Redirect target shows canonical case (e.g. `nex-agi/Nex-N2.5-mini` not `nex-agi/Nex-n2.5-mini`)
- **Gated repo handling**: 401 means repo exists but license acceptance required; token alone is not enough — must also accept license on the account
- **Tokenizer sourcing**: Lists siblings, filters filenames containing `token`; prefers `tokenizer.json` (fast) or `tokenizer.model` (SentencePiece)
- **Quant repo verification**: Shares base tokenizer but must verify `tokenizer.json` exists in the quant repo itself
- **GGUF repo fallback**: Usually bundles `tokenizer.json` — valid fallback when canonical repo is gated
- **Gotchas**: Model cards may name repos that have since been renamed or gated; `private: true` repos 404 anonymously; rate limits are generous for anonymous reads

## Features

| Feature | Detail |
|---|---|
| **Live API check** | `GET https://huggingface.co/api/models/<id>` is the source of truth |
| **Casing awareness** | 307 redirects to canonical case; store canonical ID for downstream use |
| **Gated detection** | 401 = gated; requires both token + license acceptance |
| **Tokenizer identification** | Filters siblings for `token` in filename; prefers `tokenizer.json` then `tokenizer.model` |
| **Quant/GGUF handling** | Verifies tokenizer exists in repo; GGUF repos often bundle it |
| **Rate limit safety** | Anonymous reads are generous; 429 means you're hammering — back off |

## Quick Start

```bash
# Quick public repo check (no auth needed)
curl -s -m 20 "https://huggingface.co/api/models/nvidia/NVIDIA-Nemotron-3-5B-V1" | python3 -c "
import json, sys
d = json.load(sys.stdin)
sibs = [s['rfilename'] for s in d.get('siblings', [])]
tok = [s for s in sibs if 'token' in s.lower()]
print('gated:', d.get('gated'), '| files:', len(sibs))
print('tokenizer files:', tok if tok else 'NONE')"

# Check with wrong casing (gets 307)
curl -s -m 20 "https://huggingface.co/api/models/wrongcase/SomeRepo" | head -5

# Auth for gated repos
curl -s -m 20 -H "Authorization: Bearer $HF_TOKEN" "https://huggingface.co/api/models/somegated/repo"

# Resolve main tokenizer.json directly
curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $HF_TOKEN" \
  "https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-NVFP4/resolve/main/tokenizer.json"
```

## Config

- `HF_TOKEN` environment variable for gated repo access (also used via `huggingface-cli login`)
- Token must have license acceptance rights; expired tokens produce explicit "token is expired" error
- Rate limits: generous for anonymous reads; 429 indicates tight loop — back off

## Contributing

Diagnose trigger phrases in classifier-project's `triggers.json` when docs get flagged by prompt-injection classifiers. Rephrase into observational/behavioral language preserving the operational point. See `classifier-safe-docs` skill for the rephrasing pattern.

## License

Open Claw — see `skill.toml` for details.

## Security

- Never print token values — liveness verdicts only
- Gated repos also need license acceptance on the account; a valid token alone is not sufficient
- Do not treat 404 as "absent" without first checking casing redirect (307)
- Rate limit safety: if you get 429s, you're doing something wrong (tight loop) — back off, don't hammer
- `private: true` repos 404 for anonymous callers — indistinguishable from absent without auth