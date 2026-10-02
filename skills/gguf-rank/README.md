# gguf-rank

[![for-the-badge](https://img.shields.io/badge/GGUF-Rank?style=for-the-badge)](https://gguf.all) [![for-the-badge](https://img.shields.io/badge/Fleet_Ranker-Top?style=for-the-badge)](https://fleet.run) [![for-the-badge](https://img.shields.io/API-25010-Online?style=for-the-badge)](http://127.0.0.1:25010)

## gguf-rank

Profiles all GGUFs in the models directory and ranks them by max stable context, tokens/sec, and perplexity. Uses fleet_ranker.ts. Triggers on: "rank models", "which model is fastest", "best for coding", "profile GGUFs", "benchmark".

### Procedure

1. Call GET http://127.0.0.1:25010/rank?dir=/home/toxic/sovereign/models
2. Format results as a ranked table: model | ctx | tps | ppl | tier
3. Recommend fast/mid/deep tier assignment per model

### Output

Markdown table, sorted by tokens/sec descending within each quant class.

### Quick start (3 commands max)

```bash
# Rank all GGUF models
curl "http://127.0.0.1:25010/rank?dir=/home/toxic/sovereign/models"

# Example output format
# Model | Max Context | TPS | PPL | Tier
# ------------|-------------|-----|-----|----------
# qwen2.5-coder-32b-q4_k_m.gguf | 32768 | 12.5 | 8.2 | fast
# qwen2.5-32b-instruct-q8_0.gguf | 32768 | 8.3 | 6.1 | mid
# deepseek-coder-32b-q2_k.gguf | 8192 | 5.2 | 12.5 | deep
```

### Architecture

Ranks all GGUF files in a directory using `fleet_ranker.ts`, evaluating three metrics per model:
- **Max stable context** — largest context horizon without OOM or corruption
- **Tokens/sec (tps)** — generation throughput benchmark
- **Perplexity (ppl)** — language modeling quality score

Results are sorted by tokens/sec descending within each quant class, then grouped into tier assignments: fast (highest tps, moderate ppl), mid (balanced), deep (lowest tps, highest ppl, highest context).

### Config / optional services

- `GET http://127.0.0.1:25010/rank` — ranking endpoint
- `dir=/home/toxic/sovereign/models` — directory to scan for GGUF files (required query param)
- Tier assignment thresholds are determined by the ranker based on observed tps/ppl distribution

### Dev / contributing

- Add new ranking metrics by extending `fleet_ranker.ts`
- Ensure tier assignments are consistent with observed data distribution
- Contributions should maintain the markdown table output format
- Test with a variety of GGUF quantizations (q2_k, q4_0, q5_0, q8_0, etc.)

### License

Open Claw — see `skill.toml` for details.

### Security

- Report shape only for secrets; never inspect values or delete SECRET entries
- Exit if ranking directory contains secret-shaped filenames — report names only, do not inspect