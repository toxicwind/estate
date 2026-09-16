#!/usr/bin/env bash
# DEPRECATED: use tools/hf-model-sync/hf_sync.ts (Bun) instead.
# Kept for reference only. Do not run.
set -euo pipefail

MODEL_DIR="${1:-/home/toxic/projects/models}"
REPO_DIR="$MODEL_DIR/repos"
mkdir -p "$REPO_DIR"

log() { echo "[$(date +%FT%T)] $*" | tee -a "$MODEL_DIR/organize.log"; }

python3 -c "import huggingface_hub" 2>/dev/null || pip install -q -U huggingface_hub[hf_xet]

declare -A REPO_SPECS=(
  ["Anbeeld/Qwen3.6-27B-DFlash-GGUF"]="
    Qwen3.6-27B-DFlash-IQ4_XS.gguf|*IQ4_XS*.gguf|Qwen3.6-27B-DFlash-IQ4_XS.gguf
    Qwen3.6-27B-DFlash-Q4_K_M.gguf|*Q4_K_M*.gguf|Qwen3.6-27B-DFlash-Q4_K_M.gguf
  "

  ["mradermacher/Qwen3.5-9B-DeepSeek-V4-Flash-i1-GGUF"]="
    Qwen3.5-9B-DeepSeek-V4-Flash-IQ4_XS.gguf|*IQ4_XS*.gguf|Qwen3.5-9B-DeepSeek-V4-Flash.i1-IQ4_XS.gguf
    Qwen3.5-9B-DeepSeek-V4-Flash-MTP-Q4_K_M.gguf|*MTP*Q4_K_M*.gguf|Qwen3.5-9B-DeepSeek-V4-Flash-MTP-Q4_K_M.gguf
  "

  ["unsloth/gemma-4-12b-it-GGUF"]="
    gemma-4-12b-it-Q4_K_M.gguf|*Q4_K_M*.gguf|gemma-4-12b-it-Q4_K_M.gguf
    mmproj-gemma4-12b-f16.gguf|*mmproj*F16*.gguf|mmproj-F16.gguf
    mmproj-gemma4-BF16.gguf|*mmproj*BF16*.gguf|mmproj-BF16.gguf
    mmproj-gemma4-F16.gguf|*mmproj*F16*.gguf|mmproj-F16.gguf
  "

  ["zaakirio/gemma-4-12b-it-uncensored-GGUF"]="
    gemma-4-12B-it-uncensored-Q4_K_M.gguf|*Q4_K_M*.gguf|gemma-4-12b-it-uncensored-Q4_K_M.gguf
  "

  ["cloudnathan5/gemma-4-12b-it-MTP-GGUF"]="
    gemma4-12b-it-mtp-Q4_K_M.gguf|*Q4_K_M*.gguf|gemma4-12b-it-mtp-Q4_K_M.gguf
  "

  ["mradermacher/StrangeMerges_19-7B-dare_ties-GGUF"]="
    StrangeMerges_19-7B-dare_ties.Q4_K_M.gguf|*Q4_K_M*.gguf|StrangeMerges_19-7B-dare_ties.Q4_K_M.gguf
  "

  ["DavidAU/MN-GRAND-Gutenburg-Lyra4-Lyra-23B-V2-GGUF"]="
    MN-GRAND-23.5B-Gutenberg-UNCENSORED-V2-Q4_K_M.gguf|*Q4_K_M*.gguf|MN-GRAND-23.5B-Gutenberg-UNCENSORED-V2-Q4_K_M.gguf
  "

  ["deucebucket/Qwen3.6-27B-Cerebellum-GGUF"]="
    Qwen3.6-27B-Cerebellum-v4-Q2_K_Mixed.gguf|Qwen3.6-27B-Cerebellum-v4-Q2_K_Mixed.gguf|Qwen3.6-27B-Cerebellum-v4-Q2_K_Mixed.gguf
    Qwen3.6-27B-Cerebellum-v5-Q2_K_Mixed.gguf|Qwen3.6-27B-Cerebellum-v5-Q2_K_Mixed.gguf|Qwen3.6-27B-Cerebellum-v5-Q2_K_Mixed.gguf
  "

  ["lambsea/Qwen3.6-27B-Abliterated-Heretic-Uncensored-UD-GGUF"]="
    heretic-UD-27B-Q4_K_XL.gguf|*Q4_K_XL*.gguf|heretic-UD-27B-Q4_K_XL.gguf
    heretic-UD-27B-Q5_K_XL.gguf|*Q5_K_XL*.gguf|heretic-UD-27B-Q5_K_XL.gguf
  "

  ["bartowski/Qwen2.5-1.5B-Instruct-GGUF"]="
    Qwen2.5-1.5B-Draft-Q8_0.gguf|*Q8_0*.gguf|Qwen2.5-1.5B-Instruct-Q8_0.gguf
  "

  ["barozp/Holo-3.1-35B-A3B-GGUF"]="
    Holo-3.1-35B-A3B-Q4_K_M.gguf|*Q4_K_M*.gguf|Holo-3.1-35B-A3B-Q4_K_M.gguf
    mmproj-holo-31-F16.gguf|*mmproj*F16*.gguf|mmproj-F16.gguf
  "

  ["LGAI-EXAONE/EXAONE-4.0-1.2B-GGUF"]="
    EXAONE-4.0-1.2B-IQ4_XS.gguf|*IQ4_XS*.gguf|EXAONE-4.0-1.2B-IQ4_XS.gguf
    EXAONE-4.0-1.2B-Q4_K_M.gguf|*Q4_K_M*.gguf|EXAONE-4.0-1.2B-Q4_K_M.gguf
    EXAONE-4.0-1.2B-Q5_K_M.gguf|*Q5_K_M*.gguf|EXAONE-4.0-1.2B-Q5_K_M.gguf
    EXAONE-4.0-1.2B-Q6_K.gguf|*Q6_K*.gguf|EXAONE-4.0-1.2B-Q6_K.gguf
    EXAONE-4.0-1.2B-Q8_0.gguf|*Q8_0*.gguf|EXAONE-4.0-1.2B-Q8_0.gguf
  "

  ["unsloth/Qwen3.6-27B-GGUF"]="
    mmproj-27B-F16.gguf|*mmproj*F16*.gguf|mmproj-27B-F16.gguf
    mmproj-qwen36-27B-F16.gguf|*mmproj*F16*.gguf|mmproj-qwen36-27B-F16.gguf
  "

  ["barozp/gemma-4-31b-it-dflash-Q4_K_M-GGUF"]="
    gemma4-31b-it-dflash-Q4_K_M.gguf|*Q4_K_M*.gguf|gemma4-31b-it-dflash-Q4_K_M.gguf
  "
)

repo_to_folder() { echo "$1" | sed 's|/|__|g'; }

download_repo_files() {
  local repo_id="$1"
  local repo_folder="$2"
  local dest_dir="$REPO_DIR/$repo_folder"
  mkdir -p "$dest_dir"

  local spec="${REPO_SPECS[$repo_id]}"
  [[ -z "$spec" ]] && return 0

  echo "$spec" | while IFS= read -r line; do
    line=$(echo "$line" | xargs)
    [[ -z "$line" ]] && continue

    IFS='|' read -r local_name pattern actual <<< "$line"
    local dest_file="$dest_dir/$local_name"

    if [[ -f "$dest_file" && -s "$dest_file" ]]; then
      echo "  ✓ $repo_folder/$local_name exists"
      continue
    fi

    local src=""
    for search_dir in "$MODEL_DIR" "$HOME/models" "$HOME/sovereign/models"; do
      if [[ -f "$search_dir/$local_name" && -s "$search_dir/$local_name" ]]; then
        src="$search_dir/$local_name"; break
      fi
      if [[ "$actual" != "$local_name" && -f "$search_dir/$actual" && -s "$search_dir/$actual" ]]; then
        src="$search_dir/$actual"; break
      fi
    done

    if [[ -n "$src" ]]; then
      echo "  → Linking $repo_folder/$local_name from $src"
      ln -sf "$src" "$dest_file"
      continue
    fi

    echo "  ↓ Downloading $local_name from $repo_id..."
    python3 << PYEOF
import sys, shutil, fnmatch
from pathlib import Path
from huggingface_hub import hf_hub_download, HfFileSystem

repo_id = "$repo_id"
pattern = "$pattern"
dest_dir = Path("$dest_dir")
target_name = "$local_name"

try:
    hffs = HfFileSystem()
    files = [f["name"] if isinstance(f, dict) else f for f in hffs.ls(repo_id, recursive=True)]
    file_list = [str(Path(f).relative_to(repo_id)) for f in files]
    matching = [f for f in file_list if fnmatch.fnmatch(f, pattern)]
    if not matching:
        print(f"ERROR: No match for {pattern} in {repo_id}")
        print(f"Available: {file_list[:30]}")
        sys.exit(1)
    match = matching[0]
    subfolder = str(Path(match).parent) if str(Path(match).parent) != "." else ""
    filename = Path(match).name

    downloaded = hf_hub_download(
        repo_id=repo_id, filename=filename,
        subfolder=subfolder if subfolder != "." else None,
        local_dir=str(dest_dir), local_dir_use_symlinks=False,
    )
    downloaded_path = Path(downloaded)
    final_path = dest_dir / target_name
    if downloaded_path.name != target_name:
        shutil.move(str(downloaded_path), str(final_path))
        print(f"RENAMED {downloaded_path.name} -> {target_name}")
    else:
        print(f"OK {target_name}")
    cache_dir = dest_dir / ".cache"
    if cache_dir.exists(): shutil.rmtree(cache_dir, ignore_errors=True)
    sys.exit(0)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
PYEOF
    [[ $? -ne 0 ]] && echo "  ✗ Failed: $local_name" && continue
  done
}

fetch_readme() {
  local repo_id="$1"
  local repo_folder="$2"
  local readme_file="$REPO_DIR/$repo_folder/README.md"
  [[ -f "$readme_file" ]] && return 0

  echo "  📄 Fetching README for $repo_id..."
  python3 << PYEOF
from pathlib import Path
from huggingface_hub import HfApi, hf_hub_download

repo_id = "$repo_id"
readme_path = Path("$readme_file")

try:
    api = HfApi()
    files = api.list_repo_files(repo_id)
    if "README.md" in files:
        downloaded = hf_hub_download(repo_id=repo_id, filename="README.md", 
                                     local_dir=str(readme_path.parent), local_dir_use_symlinks=False)
        Path(downloaded).rename(readme_path) if Path(downloaded).name != "README.md" else None
        print("README downloaded")
    else:
        print("No README.md in repo")
except Exception as e:
    print(f"Could not fetch README: {e}")
PYEOF
}

echo "=== Organizing models into $REPO_DIR ==="
for repo_id in "${!REPO_SPECS[@]}"; do
  repo_folder=$(repo_to_folder "$repo_id")
  echo ""
  echo "Processing: $repo_id -> $repo_folder"
  
  download_repo_files "$repo_id" "$repo_folder"
  fetch_readme "$repo_id" "$repo_folder"
done

echo ""
echo "=== Creating symlinks in $MODEL_DIR ==="
for repo_id in "${!REPO_SPECS[@]}"; do
  repo_folder=$(repo_to_folder "$repo_id")
  spec="${REPO_SPECS[$repo_id]}"
  
  echo "$spec" | while IFS= read -r line; do
    line=$(echo "$line" | xargs)
    [[ -z "$line" ]] && continue
    IFS='|' read -r local_name pattern actual <<< "$line"
    
    src="$REPO_DIR/$repo_folder/$local_name"
    dest="$MODEL_DIR/$local_name"
    
    if [[ -f "$src" && ! -L "$dest" ]]; then
      ln -sf "$src" "$dest"
      echo "  → $local_name -> repos/$repo_folder/$local_name"
    elif [[ -L "$dest" ]]; then
      # Update symlink if needed
      ln -sf "$src" "$dest"
    fi
  done
done

echo ""
echo "=== Done ==="
echo "Organized in: $REPO_DIR"
echo "Symlinks in:  $MODEL_DIR"
echo ""
echo "Structure:"
find "$REPO_DIR" -maxdepth 2 -type f \( -name "*.gguf" -o -name "README.md" \) | sort | sed "s|$REPO_DIR/|  |"

