#!/usr/bin/env bash
# refresh-groq.sh — Fetch live Groq model list and update tau groq.json
# Usage: GROQ_API_KEY=... ./refresh-groq.sh
#
# Requires: curl, jq
# Dependencies: GROQ_API_KEY environment variable

set -euo pipefail

BASE_URL="https://api.groq.com/openai/v1"
MODELS_ENDPOINT="${BASE_URL}/models"
GROQ_JSON="packages/ai/src/providers/data/groq.json"
ENGINE_GROQ_JSON="engine/packages/ai/src/providers/data/groq.json"

if [ -z "${GROQ_API_KEY:-}" ]; then
	echo "ERROR: GROQ_API_KEY environment variable not set"
	echo "Usage: GROQ_API_KEY=... ./refresh-groq.sh"
	exit 1
fi

echo "Fetching live Groq models from ${MODELS_ENDPOINT}..."

# Fetch live models
RESPONSE=$(curl -s -f -H "Authorization: Bearer ${GROQ_API_KEY}" "${MODELS_ENDPOINT}")
if [ $? -ne 0 ]; then
	echo "ERROR: Failed to fetch models from Groq API"
	exit 1
fi

echo "Response received. Parsing..."

# Extract model list from response
MODEL_COUNT=$(echo "$RESPONSE" | jq '.data | length')
echo "Found ${MODEL_COUNT} models from Groq API"

# Pretty-print the full response for inspection
echo ""
echo "=== Full API Response ==="
echo "$RESPONSE" | jq '.'

# Generate updated groq.json entries from live data
echo ""
echo "=== Model IDs ==="
echo "$RESPONSE" | jq -r '.data[].id'

# Update groq.json with live model context windows
echo ""
echo "Updating ${GROQ_JSON} and ${ENGINE_GROQ_JSON}..."

# For each model in the live response, update context_window and maxTokens
echo "$RESPONSE" | jq --argjson models "$(cat "$GROQ_JSON")" '
  .data as $live_models |
  $models |
  .openai-completions as $existing |
  reduce $live_models[] as $m (
    $existing;
    .[$m.id] = (
      if .[$m.id] then
        .[$m.id] | .context_window = ($m.context_window // .context_window)
      else
        $m | {
          id: .id,
          name: (.name // .id),
          api: "openai-completions",
          provider: "groq",
          baseUrl: "https://api.groq.com/openai/v1",
          reasoning: false,
          input: ["text"],
          cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
          contextWindow: (.context_window // 131072),
          maxTokens: (.context_window // 131072),
          streaming: true
        }
      end
    )
  ) |
  { "openai-completions": . }
' > /tmp/groq_updated.json

# Copy updated file to both locations
cp /tmp/groq_updated.json "$GROQ_JSON"
cp /tmp/groq_updated.json "$ENGINE_GROQ_JSON"

echo ""
echo "Done! Updated groq.json and engine groq.json with ${MODEL_COUNT} models."
echo "Review the changes before committing."
