#!/usr/bin/env bash
# yote-embed launcher (pitchfork-supervised).
# Local embedding server for OpenFang memory — yote RTX 3090, not external GPU APIs.
# Model: nomic-embed-text-v1.5 Q8_0 (768 dims).
set -euo pipefail
BIN=/home/toxic/sovereign/engines/herd/beellama.cpp/build-cuda86/bin/llama-server
MODEL=/home/toxic/models/nomic-embed-text-v1.5-Q8_0.gguf
export LD_LIBRARY_PATH=/home/toxic/sovereign/engines/herd/beellama.cpp/build-cuda86/bin
export CUDA_VISIBLE_DEVICES=0
exec "$BIN" --model "$MODEL" --host 127.0.0.1 --port 25200 --embedding --n-gpu-layers 99 --parallel 1 --metrics
