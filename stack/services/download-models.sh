#!/usr/bin/env bash
# download-models.sh
# Fetch recommended GGUF models for the Sovereign Stack
# Run: ./download-models.sh

set -euo pipefail

SOV="${SOVEREIGN_ROOT:-/home/toxic/sovereign}"
MODELS_DIR="${SOV}/models"
mkdir -p "$MODELS_DIR"

echo "=== Sovereign Model Downloader ==="
echo "Target directory: $MODELS_DIR"
echo ""

# Check for hf
if ! command -v hf &>/dev/null; then
    echo "Installing huggingface-hub..."
    pip install -q huggingface-hub hf-transfer
fi

export HF_XET_HIGH_PERFORMANCE=1

download_model() {
    local repo="$1"
    local pattern="$2"
    local target="$3"

    if [ -f "$target" ]; then
        echo "✓ $target already exists, skipping"
        return 0
    fi

    echo "Downloading $repo ($pattern)..."
    hf download "$repo" \
        --local-dir "$MODELS_DIR" \
        --include "$pattern"
    echo "✓ $target downloaded"
}

echo "--- Tier 1: Large Context + Reasoning (128K) ---"

# Qwen3-32B Q4_K_M (~19-20GB VRAM)
download_model \
    "Qwen/Qwen3-32B-GGUF" \
    "*Q4_K_M*" \
    "$MODELS_DIR/Qwen3-32B-Q4_K_M.gguf"

# DeepSeek-R1-Distill-Qwen-32B Q4_K_M (~18GB VRAM)
download_model \
    "lmstudio-community/DeepSeek-R1-Distill-Qwen-32B-GGUF" \
    "*Q4_K_M*" \
    "$MODELS_DIR/DeepSeek-R1-Distill-Qwen-32B-Q4_K_M.gguf"

# QwQ-32B Q4_K_M (~18GB VRAM)
download_model \
    "unsloth/QwQ-32B-GGUF" \
    "*Q4_K_M*" \
    "$MODELS_DIR/QwQ-32B-Q4_K_M.gguf"

echo ""
echo "--- Tier 2: Medium Context + Coding (128K) ---"

# Qwen3-14B Q6_K (~11GB VRAM)
download_model \
    "Qwen/Qwen3-14B-GGUF" \
    "*Q6_K*" \
    "$MODELS_DIR/Qwen3-14B-Q6_K.gguf"

# Qwen3-8B Q8_0 (~8.5GB VRAM)
download_model \
    "Qwen/Qwen3-8B-GGUF" \
    "*Q8_0*" \
    "$MODELS_DIR/Qwen3-8B-Q8_0.gguf"

echo ""
echo "--- Warmup Model ---"

# Your existing warmup model (update path as needed)
if [ ! -f "$MODELS_DIR/qwen-flash.gguf" ]; then
    echo "⚠ qwen-flash.gguf not found. Place your warmup model at:"
    echo "   $MODELS_DIR/qwen-flash.gguf"
fi

echo ""
echo "=== Download Summary ==="
ls -lh "$MODELS_DIR"/*.gguf 2>/dev/null || echo "No models downloaded yet"
echo ""
echo "Total disk usage:"
du -sh "$MODELS_DIR"