#!/usr/bin/env bash
# beellama-fast — exaone-4.0-1.2b-iq4xs ("fast" alias) via beellama.cpp fork v0.4.6 CUDA build.
# Permanent supervised OpenAI-compatible endpoint on BEELLAMA_PORT (SSOT).
# Bench 2026-09-20 (RTX 3090): pp 15.6k tok/s, gen 311-335 tok/s.
# Lifecycle owned by pitchfork; this script does NOT kill or steal the port.
set -euo pipefail
SOV="$HOME/sovereign"
source "$SOV/stack/lib-ports.sh"
# 2026-09-20: default the SSOT port so a spawn without env (pitchfork retry path) cannot hit llama-server --port stoi
BEELLAMA_PORT="${BEELLAMA_PORT:-25122}"
require_port BEELLAMA_PORT
ENGINE="$HOME/projects/sovereign-projects/herd/engines/beellama.cpp/build-cuda86/bin"
BIN="$ENGINE/llama-server"
[[ -x "$BIN" ]] || { echo "beellama-fast: bin not found at $BIN" >&2; exit 1; }
MODEL="$HOME/models/EXAONE-4.0-1.2B-IQ4_XS.gguf"
[[ -f "$MODEL" ]] || { echo "beellama-fast: model not found at $MODEL" >&2; exit 1; }
export LD_LIBRARY_PATH="$ENGINE${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export CUDA_VISIBLE_DEVICES=0
exec "$BIN" --model "$MODEL" \
  --host 127.0.0.1 --port "$BEELLAMA_PORT" \
  --n-gpu-layers all --flash-attn on --parallel 1 --metrics --mlock --no-mmap \
  --kv-unified --no-host --cache-ram 0 \
  --ctx-size 32768 -b 2048 -ub 512 \
  --cache-type-k q8_0 --cache-type-v q8_0 \
  --alias fast
