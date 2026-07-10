#!/usr/bin/env bash
set -euo pipefail
MODEL_DIR="${MODEL_DIR:-/home/toxic/sovereign/models}"
mkdir -p "$MODEL_DIR"; cd "$MODEL_DIR"
export HF_XET_HIGH_PERFORMANCE=1
export HF_XET_NUM_CONCURRENT_RANGE_GETS=24
unset HF_DEBUG

download() {
  local target="$1" repo="$2" pattern="$3"
  if [ -f "$target" ]; then echo "✅ $target"; return 0; fi
  echo "⬇️  $target <- $repo [$pattern]"
  hf download "$repo" --include "$pattern" --local-dir . || echo "⚠️ 404/gated $repo"
  local found=$(find . -maxdepth 3 -type f -name "$pattern" -printf "%T@ %p\n" 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
  [ -z "$found" ] && found=$(find . -maxdepth 3 -type f -name "$target" | head -1)
  [ -n "$found" ] && [ "$found" != "./$target" ] && mv -n "$found" "./$target" 2>/dev/null && echo "✔ $target" || true
}

# === YOUR STACK + MY VERIFIED ===
download "gemma-4-12b-it-Q4_K_M.gguf" "unsloth/gemma-4-12b-it-GGUF" "*Q4_K_M*.gguf"
download "mmproj-gemma4-12b-f16.gguf" "unsloth/gemma-4-12b-it-GGUF" "*mmproj*F16*.gguf"
download "mmproj-BF16.gguf" "unsloth/gemma-4-12b-it-GGUF" "mmproj-BF16.gguf"
download "gemma-4-12b-it-uncensored-Q4_K_M.gguf" "zaakirio/gemma-4-12b-it-uncensored-GGUF" "*Q4_K_M*.gguf"
download "gemma4-12b-it-mtp-Q4_K_M.gguf" "barozp/gemma4-12b-it-mtp-GGUF" "*Q4_K_M*.gguf"
download "gemma-4-21b-a4b-it-REAP-Q4_K_M.gguf" "barozp/gemma-4-21b-a4b-it-REAP-GGUF" "*Q4_K_M*.gguf"
download "gemma-4-19b-a4b-it-REAP-Q4_K_M.gguf" "barozp/gemma-4-19b-a4b-it-REAP-GGUF" "*Q4_K_M*.gguf"
download "Qwen-3.5-28B-A3B-REAP-Q4_K_M.gguf" "barozp/Qwen-3.5-28B-A3B-REAP-GGUF" "*Q4_K_M*.gguf"
download "ZAYA1-8B-Q4_K_M.gguf" "barozp/ZAYA1-8B-BNB" "*Q4_K_M*.gguf"
download "Qwen3.5-9B-DeepSeek-V4-Flash-MTP-BF16.gguf" "Jackrong/Qwen3.5-9B-DeepSeek-V4-Flash-MTP-GGUF" "*BF16*.gguf"
download "ornith-9b-dflash.gguf" "onion515/ornith-9b-dflash" "ornith-9b-dflash.gguf"; ln -sf ornith-9b-dflash.gguf Qwen3.5-9B-DFlash-Q5_K_M.gguf
download "Qwen3.6-27B-Cerebellum-v4.gguf" "deucebucket/Qwen3.6-27B-Cerebellum-GGUF" "Qwen3.6-27B-Cerebellum-v4.gguf"
download "mmproj-27B-F16.gguf" "unsloth/Qwen3.6-27B-GGUF" "*mmproj*F16*.gguf"
download "Qwen3.6-27B-DFlash-IQ4_XS.gguf" "Anbeeld/Qwen3.6-27B-DFlash-GGUF" "*IQ4_XS*.gguf"
download "Qwen3.6-27B-MTP-UD-Q4_K_XL.gguf" "unsloth/Qwen3.6-27B-MTP-GGUF" "*Q4_K_XL*.gguf"
download "MN-GRAND-23.5B-Gutenberg-UNCENSORED-V2-Q6_K.gguf" "DavidAU/MN-GRAND-Gutenburg-Lyra4-Lyra-23B-V2-GGUF" "*Q6*.gguf"
download "Qwen2.5-1.5B-Draft-Q8_0.gguf" "bartowski/Qwen2.5-1.5B-Instruct-GGUF" "*Q8_0*.gguf"
download "heretic-UD-27B-Q4_K_XL.gguf" "lambsea/Qwen3.6-27B-Abliterated-Heretic-Uncensored-UD-GGUF" "*Q4_K_XL*.gguf"

# === NEW 16 FROM YOUR OSINT TABLE (add even if unverified) ===
# 1 deucebucket Cerebellum - already above
# 2 Jackrong MTP Q4_K_M ~5.4GB (you had BF16, this adds Q4)
download "Jackrong-Qwen3.5-9B-MTP-Q4_K_M.gguf" "Jackrong/Qwen3.5-9B-DeepSeek-V4-Flash-MTP-GGUF" "*Q4_K_M*.gguf"
# 3 barozp Holo-3.1-35B-A3B MoE VLM 262k
download "Holo-3.1-35B-A3B-Q4_K_M.gguf" "barozp/Holo-3.1-35B-A3B-GGUF" "*Q4_K_M*.gguf"
download "Holo-mmproj-F16.gguf" "barozp/Holo-3.1-35B-A3B-GGUF" "*mmproj*.gguf"
# 4 prithiv DA
download "Q3.5-9B-DS-v4-Flash-DA-Q4_K_M.gguf" "prithivMLmods/Q3.5-9B-DS-v4-Flash-DA" "*Q4_K_M*.gguf"
# 5 DavidAU MN-Oblivion 26B 89 layers
download "MN-Oblivion-26B-Q6_K.gguf" "DavidAU/MN-Oblivion-26B-UNCENSORED-NEO-Imatrix-GGUF" "*Q6_K*.gguf"
download "MN-Oblivion-26B-Q4_K_M.gguf" "DavidAU/MN-Oblivion-26B-UNCENSORED-NEO-Imatrix-GGUF" "*Q4_K_M*.gguf"
# 6 AtomicChat Imatrix
download "AtomicChat-gemma-4-12b-it-Q4_K_M.gguf" "AtomicChat/gemma-4-12b-it-GGUF" "*Q4_K_M*.gguf"
# 7 igorls QAT Q4_0 Heretic - new
download "igorls-gemma-4-12B-qat-q4_0-heretic.gguf" "igorls/gemma-4-12B-it-qat-q4_0-heretic-GGUF" "*q4_0*.gguf"
download "igorls-gemma-4-12B-qat-Q4_K_M.gguf" "igorls/gemma-4-12B-it-qat-q4_0-heretic-GGUF" "*Q4_K_M*.gguf"
# 8 zaakirio MTP draft 444MB
download "zaakirio-gemma-4-12b-uncensored-MTP.gguf" "zaakirio/gemma-4-12b-it-uncensored-GGUF" "*mtp*.gguf"
download "zaakirio-mtp-444MB.gguf" "zaakirio/gemma-4-12b-it-uncensored-GGUF" "*444*.gguf"
# 9 unsloth MTP UD already above, add Q4_K_M variant
download "unsloth-Qwen3.6-27B-MTP-Q4_K_M.gguf" "unsloth/Qwen3.6-27B-MTP-GGUF" "*Q4_K_M*.gguf"
# 10 maxkru92 Opus MTP
download "maxkru92-gemma-4-12B-Opus-MTP-Q8_0.gguf" "maxkru92/gemma-4-12B-it-Claude-4.6-4.8-Opus-GGUF" "*Q8_0*.gguf"
download "maxkru92-gemma-4-12B-Opus-MTP-Q4_K_M.gguf" "maxkru92/gemma-4-12B-it-Claude-4.6-4.8-Opus-GGUF" "*Q4_K_M*.gguf"
# 11 onion515 already
# 12 Ardenzard DFlash 27B IQ4_XS 892MB
download "Ardenzard-Qwen3.6-27B-DFlash-IQ4_XS.gguf" "Ardenzard/Qwen3.6-27B-DFlash-GGUF" "*IQ4_XS*.gguf"
# 13 DavidAU MN-GRAND GLM4.7 Thinking
download "MN-GRAND-GLM4.7-Thinking-Q6_K.gguf" "DavidAU/MN-GRAND-GLM4.7-Thinking-GGUF" "*Q6_K*.gguf"
download "MN-GRAND-GLM4.7-Thinking-Q4_K_M.gguf" "DavidAU/MN-GRAND-GLM4.7-Thinking-GGUF" "*Q4_K_M*.gguf"
# 14 mradermacher i1 Imatrix + mmproj
download "mradermacher-Qwen3.5-9B-Flash-i1-Q4_K_M.gguf" "mradermacher/Qwen3.5-9B-DeepSeek-V4-Flash-i1-GGUF" "*Q4_K_M*.gguf"
download "mradermacher-mmproj-F16.gguf" "mradermacher/Qwen3.5-9B-DeepSeek-V4-Flash-i1-GGUF" "*mmproj*.gguf"
# 15 cHunter789 IQ4_XS 14.5GB
download "cHunter-Qwen3.6-27B-i1-IQ4_XS.gguf" "cHunter789/Qwen3.6-27B-i1-IQ4_XS-GGUF" "*IQ4_XS*.gguf"
# 16 llmfan46 Heretic-Cerebellum v2 baseline
download "llmfan46-Heretic-Cerebellum-27B-v2-Q2_K_Mixed.gguf" "llmfan46/Heretic-Cerebellum-27B-v2-GGUF" "*Q2_K_Mixed*.gguf"
download "llmfan46-Gemma-4-Garnet-31B-heretic-Q4_K_M.gguf" "llmfan46/Gemma-4-Garnet-31B-it-uncensored-heretic-GGUF" "*Q4_K_M*.gguf"

# === YOUR EXTRA HOLO/MN-Oblivion/Deckard placeholders ===
download "Qwen3.6-40B-Deckard-MTP-IQ4_XS.gguf" "PiehSoft/Qwen3.6-40B-Deckard-MTP" "*IQ4_XS*.gguf"
download "Qwopus3.6-35B-A3B-v1-MTP-Q4_K_M.gguf" "Jackrong/Qwopus3.6-35B-A3B-v1-MTP-GGUF" "*Q4_K_M*.gguf"

find . -type d -empty -delete; chmod 644 *.gguf 2>/dev/null || true
ls -lh *.gguf | awk '{print $9, $5}' | sort -k2 -h | tail -60