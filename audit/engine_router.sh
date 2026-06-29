#!/bin/bash
set -euo pipefail

ENGINE_FILE="/home/toxic/sovereign/.current_engine"
DEFAULT_ENGINE="beellama"
SELECTED_ENGINE=$(cat "$ENGINE_FILE" 2>/dev/null || echo "$DEFAULT_ENGINE")

BASE_FLAGS="-m /home/toxic/models/Qwen3.5-9B-DeepSeek-V4-Flash-IQ4_XS.gguf --host 0.0.0.0 --port 25001 -c 196608 --parallel 1 -b 4096 -ub 1024 --flash-attn 1 -ngl 99 -t 2 --no-mmap --embeddings --pooling cls"

if [ "$SELECTED_ENGINE" = "beellama" ]; then
    echo "Launching Native TCQ + DFlash Engine Fabric"
    exec /home/toxic/beellama.cpp/build/bin/llama-server ${BASE_FLAGS} \
      --cache-type-k turbo3_tcq \
      --cache-type-v turbo3_tcq \
      --spec-type none \
      --reasoning-loop-window 2048 \
      --reasoning-loop-max-period 32
else
    echo "Launching Standard Turboquant Reference"
    exec /home/toxic/llama-cpp-turboquant/build/bin/llama-server ${BASE_FLAGS} \
      -ctk turbo3 \
      -ctv turbo3
fi
