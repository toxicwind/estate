#!/usr/bin/env bash
set -euo pipefail

exec /home/toxic/ik_llama.cpp-main/build/bin/llama-server \
  -m "/home/toxic/models/Qwen3.6-27B-Heretic-UD/heretic-UD-27B-Q5_K_XL.gguf" \
  --mmproj "/home/toxic/models/Qwen3.6-27B-Heretic-UD/mmproj-27B-F16.gguf" \
  -c 262144 \
  --parallel 3 \
  -ctk q8_0 -ctv q8_0 \
  --flash-attn 1 \
  -ngl 99 \
  -t 8 \
  -cram -1 \
  --alias qwen3.5 \
  --webui llamacpp \
  --jinja \
  --merge-qkv \
  --grouped-expert-routing \
  --reasoning-format auto \
  --host 127.0.0.1 \
  --port 25001
