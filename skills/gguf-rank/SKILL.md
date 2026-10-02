---
name: gguf-rank
description: >
  GGUF model profiling and ranking. Calls the rank service on port 25010 to measure each GGUF's max stable context, tokens/sec and perplexity, then reports a fast/mid/deep tier table. Triggers on: "gguf rank", "context length", "tokens per second", "model ranking".
---

# GGUF Rank Skill

## Procedure

1. Call GET http://127.0.0.1:25010/rank?dir=/home/toxic/sovereign/models
2. Format results as a ranked table: model | ctx | tps | ppl | tier
3. Recommend fast/mid/deep tier assignment per model

## Output

Markdown table, sorted by tokens/sec descending within each quant class.
