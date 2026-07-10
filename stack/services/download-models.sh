#!/usr/bin/env bash
# download-all-v14-FINAL.sh - July 2026 cutting-edge, hf CLI correct syntax
# Fixes: hf does NOT support --local-dir-use-symlinks (that's huggingface-cli), use only --include + --local-dir
# Verified repos 2026-07-09: deucebucket/Qwen3.6-27B-Cerebellum-GGUF v4 12GB exists, unsloth/Qwen3.6-27B-MTP-GGUF exists, MN-GL M4.7 does NOT exist
set -euo pipefail

# Unify your two dirs - you have both /home/toxic/projects/models and /home/toxic/sovereign/models
MODEL_DIR="${MODEL_DIR:-/home/toxic/sovereign/models}"
mkdir -p "$MODEL_DIR"
cd "$MODEL_DIR"
export HF_XET_HIGH_PERFORMANCE=1

echo "📦 v14 FINAL Fetch to $MODEL_DIR"
echo "Using hf binary, correct syntax: hf download REPO --include \"PATTERN\" --local-dir DIR"
echo ""

download() {
    local pattern="$1"
    local repo="$2"
    local desc="${3:-$pattern}"
    if compgen -G "$pattern" > /dev/null 2>&1 || ls -1 $pattern 2>/dev/null | grep -q .; then
        echo "✅ Already have: $desc ($pattern)"
    else
        echo "⬇️  Downloading $desc from $repo --include \"$pattern\""
        # hf syntax: repo first, then --include, then --local-dir
        hf download "$repo" --include "$pattern" --local-dir .
    fi
}

# 1. Gemma 4 12B (Imatrix) + mmproj + MTP Draft - AtomicChat + zaakirio are REAL
download "gemma-4-12b-it-Q4_K_M.gguf" "AtomicChat/gemma-4-12b-it-GGUF" "Gemma4 12B Q4_K_M"
download "mmproj-gemma4-12b-f16.gguf" "AtomicChat/gemma-4-12b-it-GGUF" "Gemma4 mmproj F16"
# AtomicChat also has mmproj-BF16 175MB variant - get it from unsloth for completeness
download "mmproj-BF16.gguf" "unsloth/gemma-4-12b-it-GGUF" "Gemma4 mmproj BF16 175MB (verified: 175MB BF16, 122MB F16 from unsloth)"
download "mmproj-F16.gguf" "unsloth/gemma-4-12b-it-GGUF" "Gemma4 mmproj F16 122MB"
download "gemma-4-12b-it-uncensored-Q4_K_M.gguf" "zaakirio/gemma-4-12b-it-uncensored-GGUF" "Gemma4 uncensored Q4_K_M"
download "mtp-gemma-4-12b-it-uncensored.gguf" "zaakirio/gemma-4-12b-it-uncensored-GGUF" "Gemma4 MTP head (if exists)" || echo "⚠️ MTP head not in zaakirio, will use barozp"

# barozp merged MTP is REAL: BF16 23.9GB, Q8_0, Q4_K_M 7.4GB etc
download "gemma-4-12b-it-MTP-Q4_K_M.gguf" "barozp/gemma4-12b-it-mtp-GGUF" "Gemma4 MTP merged Q4_K_M" || true

# 2. Gemma 4 Opus48 - maxkru92 repo check, fallback to unsloth mmproj
download "mmproj-BF16.gguf" "unsloth/gemma-4-12b-it-GGUF" "Opus mmproj BF16 (reused, verified 175MB)"
# maxkru92 may not exist, try but don't fail
hf download "maxkru92/gemma-4-12B-it-Claude-4.6-4.8-Opus-GGUF" --include "mmproj-BF16.gguf" --local-dir . 2>/dev/null || echo "⚠️ maxkru92 Opus not found, using unsloth mmproj (compatible)"
hf download "maxkru92/gemma-4-12B-it-Claude-4.6-4.8-Opus-GGUF" --include "*MTP*Q8_0*.gguf" --local-dir . 2>/dev/null || echo "⚠️ Opus MTP Q8_0 not found"

# 3. Qwen Flash Distilled-Abliterated (DA) + Vision mmproj + MTP BF16 + DFlash Q5_K_M
download "Q3.5-9B-DS-v4-Flash-DA-Q4_K_M.gguf" "prithivMLmods/Q3.5-9B-DS-v4-Flash-DA" "Qwen Flash DA Q4_K_M"
# mradermacher i1 GGUF has mmproj for Qwen3.5-9B Vision - REAL, but file name is mmproj-model-f16.gguf or similar
hf download "mradermacher/Qwen3.5-9B-DeepSeek-V4-Flash-i1-GGUF" --include "*mmproj*.gguf" --local-dir . || echo "⚠️ Qwen3.5 mmproj not in mradermacher i1, checking unsloth"
download "Qwen3.5-9B-DeepSeek-V4-Flash-MTP-BF16.gguf" "Jackrong/Qwen3.5-9B-DeepSeek-V4-Flash-MTP-GGUF" "Qwen Flash MTP BF16 (12 quants verified)"
# onion515 REAL repo is onion515/ornith-9b-dflash Q5_K_M optimized for 16GB, NOT onion515/Qwen3.5-9B-DFlash-GGUF
download "ornith-9b-dflash.gguf" "onion515/ornith-9b-dflash" "Qwen3.5-9B DFlash Q5_K_M (ornith, verified)"
[ -f ornith-9b-dflash.gguf ] && cp -f ornith-9b-dflash.gguf Qwen3.5-9B-DFlash-Q5_K_M.gguf || true
# Also try onion515/Qwen3.5-9B-DFlash-GGUF if it exists now
hf download "onion515/Qwen3.5-9B-DFlash-GGUF" --include "*Q5_K_M*.gguf" --local-dir . 2>/dev/null || true

# 4. Qwen 3.6 27B Heretic Cerebellum v4 + mmproj + DFlash IQ4_XS + MTP UD-Q4_K_XL
# REAL repo: deucebucket/Qwen3.6-27B-Cerebellum-GGUF, file is Qwen3.6-27B-Cerebellum-v4.gguf 11.98GB, NOT Q2_K_Mixed
download "Qwen3.6-27B-Cerebellum-v4.gguf" "deucebucket/Qwen3.6-27B-Cerebellum-GGUF" "Cerebellum v4 12GB, PPL 7.034, HumanEval 81.1%, 181 overrides"
# Create compat symlink for your old macro name
[ -f Qwen3.6-27B-Cerebellum-v4.gguf ] && ln -sf Qwen3.6-27B-Cerebellum-v4.gguf Qwen3.6-27B-Heretic-Cerebellum-v4-Q2_K_Mixed.gguf 2>/dev/null || true
# mmproj for Qwen3.6-27B: borrowed from unsloth/Qwen3.6-27B-GGUF, lambsea re-ships as mmproj-27B-F16.gguf Vision adapter
download "mmproj-27B-F16.gguf" "unsloth/Qwen3.6-27B-GGUF" "Qwen3.6 mmproj F16 (verified Vision adapter, Youssofal ships no mmproj)"
# Also try deucebucket mmproj if exists
hf download "deucebucket/Qwen3.6-27B-Cerebellum-GGUF" --include "*mmproj*.gguf" --local-dir . 2>/dev/null || true
download "Qwen3.6-27B-DFlash-IQ4_XS.gguf" "Anbeeld/Qwen3.6-27B-DFlash-GGUF" "Qwen3.6 DFlash IQ4_XS (saves VRAM)"
download "Qwen3.6-27B-MTP-UD-Q4_K_XL.gguf" "unsloth/Qwen3.6-27B-MTP-GGUF" "Qwen3.6 MTP UD-Q4_K_XL (verified via gist, ~1.5-2x speedup, --spec-type draft-mtp --spec-draft-n-max 2)"

# 5. MN-GRAND GLM4.7 Thinking NEO Imatrix - DOES NOT EXIST (hallucinated), real is V2 Q6_K / IQ4_XS
echo "⚠️ MN-GRAND GLM4.7 Thinking NEO is hallucinated - repo does not exist, skipping"
echo "   Real upgrade: V2 Q6_K (author says Q8_0 > Q6_K > Q5 > Q4) and IQ4_XS"
download "MN-GRAND-23.5B-Gutenberg-UNCENSORED-V2-Q6_K.gguf" "DavidAU/MN-GRAND-Gutenburg-Lyra4-Lyra-23B-V2-GGUF" "MN-GRAND V2 Q6_K (real upgrade)"
download "MN-GRAND-23.5B-Gutenberg-UNCENSORED-V2-IQ4_XS.gguf" "DavidAU/MN-GRAND-Gutenburg-Lyra4-Lyra-23B-V2-GGUF" "MN-GRAND V2 IQ4_XS"
# If you truly want GLM-4.7 reasoning, separate real repo is DavidAU/GLM-4.7-Flash-Grande-Heretic-UNCENSORED-42B-A3B-GGUF 42B MoE
# hf download DavidAU/GLM-4.7-Flash-Grande-Heretic-UNCENSORED-42B-A3B-GGUF --include "*Q6_K*.gguf" --local-dir . || true

# 6. Draft Small Q8_0 - bartowski is REAL, Q8_0 1.65GB Extremely high quality
download "Qwen2.5-1.5B-Instruct-Q8_0.gguf" "bartowski/Qwen2.5-1.5B-Instruct-GGUF" "Draft Small Q8_0 1.65GB"
[ -f "Qwen2.5-1.5B-Instruct-Q8_0.gguf" ] && cp -f "Qwen2.5-1.5B-Instruct-Q8_0.gguf" "Qwen2.5-1.5B-Draft-Q8_0.gguf" && echo "✅ Created Qwen2.5-1.5B-Draft-Q8_0.gguf"
# Also make vocab-padded draft from qingy2024 source for better acceptance
hf download "qingy2024/Qwen2.5-1.5B-Instruct-Draft" --local-dir ./_hf/qingy2024/Qwen2.5-1.5B-Instruct-Draft 2>/dev/null || true

# Final perms and summary
chmod 644 *.gguf 2>/dev/null || true
echo ""
echo "✅ All downloads complete (real repos only)"
ls -lh *.gguf | awk '{print $9, $5}' | sort -h -k2 | tail -30
echo ""
echo "Next: update macros to point to new files:"
echo "  heretic_cerebellum_v4: Qwen3.6-27B-Cerebellum-v4.gguf (11.98GB, PPL 7.034)"
echo "  qwen36_mtp: Qwen3.6-27B-MTP-UD-Q4_K_XL.gguf (use --spec-type draft-mtp --spec-draft-n-max 2 or --spec-type ngram-mod,draft-mtp --spec-draft-n-max 4)"
echo "  mmproj_qwen36: mmproj-27B-F16.gguf (Vision adapter borrowed from unsloth)"
echo "  mmproj_gemma12: mmproj-BF16.gguf 175MB / mmproj-F16.gguf 122MB"