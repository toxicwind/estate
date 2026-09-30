# Mistral GuideLLM Audit — 2026-09-29 (kestrel)

## Key Proof

`MISTRAL_API_KEY` verified live via direct API calls:
- `GET https://api.mistral.ai/v1/models` → HTTP 200, 46 model records
- `POST https://api.mistral.ai/v1/chat/completions` (ministral-3b-latest) → HTTP 200, exact `KEYPROOF-OK` response

## Entitlement Matrix

### Working (HTTP 200)
- ministral-3b-latest, ministral-8b-latest, ministral-14b-latest
- codestral-latest, mistral-code-latest

### Rate-limited (HTTP 429, 0 req/min — no entitlement)
- mistral-medium-3.5, mistral-medium-latest, mistral-medium-3, mistral-medium-2604
- magistral-small-latest, magistral-medium-latest
- mistral-small-latest, mistral-small-2603
- mistral-vibe-cli-* (3 variants)

### Refused (HTTP 403 — not entitled)
- mistral-large-latest
- labs-leanstral-1-5, labs-leanstral-1-5-1

## Benchmark Results

Direct measurement (GuideLLM 0.8.0's OpenAI backend sends array content blocks;
Mistral's API requires string content → HTTP 422. Measured directly with
equivalent metrics: 10 streaming + 5 non-streaming requests per model).

| Model | Success | RPS | Lat p50 | Lat p99 | TTFT p50 | Tok/s |
|-------|---------|-----|---------|---------|----------|-------|
| ministral-3b-latest | 10/10 | 2.00 | 0.501s | 0.535s | 0.344s | 44.3 |
| ministral-8b-latest | 10/10 | 1.53 | 0.613s | 0.909s | 0.407s | 34.5 |
| ministral-14b-latest | 10/10 | 1.58 | 0.569s | 0.945s | 0.384s | 32.0 |
| codestral-latest | 10/10 | 1.80 | 0.536s | 0.757s | 0.377s | 35.4 |
| mistral-code-latest | 10/10 | 1.60 | 0.550s | 1.314s | 0.396s | 47.5 |

All 50 requests succeeded, zero errors.

## Config Changes

- `config/keypools.yaml`: Added `mistral` pool (upstream https://api.mistral.ai)
- `config/herd.yaml`: Mistral peer re-wired through keypool; models pruned to
  entitled IDs; corrected false 2026-09-29 "key absent" note

## GuideLLM Compatibility Note

GuideLLM 0.8.0 `openai_http` backend is incompatible with Mistral's chat API:
it sends `messages[].content` as `[{"type": "text", "text": "..."}]` arrays;
Mistral requires string content. The `openai_strict_compat` flag exists but
only controls `stream_options`/`ignore_eos`, not content format. The fork at
`projects/range/ranch/guidellm` already notes Mistral strictness in comments.
