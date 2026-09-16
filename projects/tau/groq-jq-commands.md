# Groq File Analysis — jq Commands

## List all groq files in the repo

```bash
fd groq --type f -0 | jq -Rs 'split("\u0000") | map(select(length>0))' > groq-files.json
```

## List all groq files under tau specifically

```bash
fd groq ~/projects/sovereign-projects/tau --type f -0 | jq -Rs 'split("\u0000") | map(select(length>0)) | sort' | jq '{count:length, files:.}' > tau-groq.json
```

## Count models in groq.json

```bash
jq '.openai-completions | keys | length' packages/ai/src/providers/data/groq.json
```

## List all model IDs

```bash
jq -r '.openai-completions | keys[]' packages/ai/src/providers/data/groq.json
```

## List deprecated models

```bash
jq -r '.openai-completions | to_entries[] | select(.value.deprecated == true) | .key' packages/ai/src/providers/data/groq.json
```

## List models with reasoning support

```bash
jq -r '.openai-completions | to_entries[] | select(.value.reasoning == true) | .key' packages/ai/src/providers/data/groq.json
```

## List models by cost (input price sorted)

```bash
jq -r '.openai-completions | to_entries[] | [.key, .value.cost.input, .value.cost.output] | @tsv' packages/ai/src/providers/data/groq.json | sort -k2 -n
```

## Validate all models have required fields

```bash
jq '
  .openai-completions | to_entries[] |
  select(
    (.value.contextWindow | type) != "number" or
    (.value.maxTokens | type) != "number" or
    (.value.cost | type) != "object" or
    (.value.cost.input | type) != "number"
  ) | .key
' packages/ai/src/providers/data/groq.json
```

## Generate models.dev-compatible descriptor

```bash
jq '{
  groq: {
    models: [.openai-completions | to_entries[] | {
      id: .key,
      name: .value.name,
      contextWindow: .value.contextWindow,
      maxTokens: .value.maxTokens,
      reasoning: .value.reasoning,
      cost: .value.cost
    }]
  }
}' packages/ai/src/providers/data/groq.json
```

## Check if GROQ_API_KEY is set and fetch live models

```bash
curl -s -H "Authorization: Bearer ${GROQ_API_KEY}" https://api.groq.com/openai/v1/models | jq '.data | length'
```

## Compare bundled vs live model count

```bash
echo "Bundled models: $(jq '.openai-completions | keys | length' packages/ai/src/providers/data/groq.json)"
echo "Live models: $(curl -s -H "Authorization: Bearer ${GROQ_API_KEY}" https://api.groq.com/openai/v1/models | jq '.data | length')"
```
