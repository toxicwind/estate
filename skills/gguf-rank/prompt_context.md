# GGUF Rank Skill

## Procedure

1. Call GET http://127.0.0.1:25010/rank?dir=/home/toxic/estate/models
2. Format results as a ranked table: model | ctx | tps | ppl | tier
3. Recommend fast/mid/deep tier assignment per model

## Output

Markdown table, sorted by tokens/sec descending within each quant class.