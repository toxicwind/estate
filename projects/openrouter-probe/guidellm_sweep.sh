#!/bin/bash
# guidellm_sweep.sh -- short GuideLLM sweep over working OpenRouter models.
# Key is read from /home/toxic/.secrets IN-PROCESS on yote, never printed.
# Rank on quality/latency/availability only -- cost is NOT a factor (Chris directive).
set -u
SECRETS=/home/toxic/.secrets
OUTDIR=/home/toxic/sovereign/projects/openrouter-probe/guidellm
mkdir -p "$OUTDIR"
KEY=$(grep -E '^[[:space:]]*(export[[:space:]]+)?OPENROUTER_API_KEY_1[[:space:]]*=' "$SECRETS" | head -1 | sed -E 's/^[[:space:]]*(export[[:space:]]+)?OPENROUTER_API_KEY_1[[:space:]]*=[[:space:]]*//; s/^"//; s/"$//')
if [ -z "$KEY" ]; then echo "KEY NOT FOUND"; exit 1; fi
echo "key loaded (${#KEY} chars, not shown)"

MODELS=(
  "nvidia/nemotron-3-super-120b-a12b:free"
  "nex-agi/nex-n2.5-mini:free"
  "nex-agi/nex-n2.5-pro:free"
  "nvidia/nemotron-3.5-lightning:free"
)

for m in "${MODELS[@]}"; do
  safe=$(echo "$m" | tr '/:' '__')
  echo "=== $m ==="
  timeout 900 guidellm run \
    --backend "kind=openai_http,target=https://openrouter.ai/api/v1,model=$m,api_key=$KEY,validate_backend=False" \
    --data kind=synthetic_text,prompt_tokens=32,output_tokens=32 \
    --profile kind=synchronous \
    --constraint kind=max_requests,count=5 \
    --tokenizer kind=huggingface_auto,model=gpt2 \
    --output "kind=json,path=$OUTDIR/${safe}.json" \
    --disable-progress 2>&1 | grep -v "$KEY" | tail -15
  echo "exit: $?"
done
echo "done: $OUTDIR"
ls -la "$OUTDIR"
