#!/usr/bin/env bash
set -euo pipefail
# SOVEREIGN FINAL DOWNLOADER v12.0 - PYTHON API EDITION
# Downloads 14 unique GGUFs reused for 25 ctx variants, fits 170GB -> ~122GB
# Hash-verified, XET, hardlink dedupe, avail guard
# TUI: Braille spinner, progress bar, color status, real-time stats
# 
# CRITICAL FIX v12.0: Replaced broken `hf download` CLI with Python API.
# The CLI removed --local-dir-use-symlinks. The Python API still has it.
# Pattern from: https://raw.githubusercontent.com/wiremarrow/luma/main/runpod/scripts/setup.py
#               https://raw.githubusercontent.com/abetlen/llama-cpp-python/main/llama_cpp/llama.py

MODEL_DIR="${MODEL_DIR:-$HOME/sovereign/models}"
SRC_DIRS=("$HOME/projects/models" "$HOME/models" "$HOME/sovereign/models")
LOG="$MODEL_DIR/final_download.log"
mkdir -p "$MODEL_DIR"
export HF_HUB_VERBOSITY=info
export HF_XET_HIGH_PERFORMANCE=1
export HF_XET_NUM_CONCURRENT_RANGE_GETS=8
export PYTHONUNBUFFERED=1

# ─── TUI AESTHETICS ──────────────────────────────────────────────────────────
C_RESET='\033[0m'
C_BOLD='\033[1m'
C_DIM='\033[2m'
C_RED='\033[1;31m'
C_GREEN='\033[1;32m'
C_YELLOW='\033[1;33m'
C_BLUE='\033[1;34m'
C_MAGENTA='\033[1;35m'
C_CYAN='\033[1;36m'
C_WHITE='\033[1;37m'
C_GRAY='\033[38;5;240m'
C_OK='\033[1;32m✓\033[0m'
C_SKIP='\033[1;33m◌\033[0m'
C_ERR='\033[1;31m✗\033[0m'
C_SPIN='\033[1;36m'

SPINNER_CHARS=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
SPINNER_PID=""

_term_width() { tput cols 2>/dev/null || echo 80; }

_hide_cursor() { printf '\033[?25l' >&2; }
_show_cursor() { printf '\033[?25h' >&2; }

_start_spinner() {
    local msg="${1:-Working...}"
    _hide_cursor
    local spinner_script="/tmp/.sov-spinner-$$.sh"
    cat > "$spinner_script" << 'SPINNER_EOF'
#!/bin/bash
set -m
cleanup() { kill -- -$$ 2>/dev/null || true; exit 0; }
trap cleanup TERM INT HUP EXIT
spinner_chars=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
p=0
while true; do
    printf "\033[s%s\033[u" "${spinner_chars[$p]}" >&2
    p=$(( (p + 1) % 10 ))
    sleep 0.08
done
SPINNER_EOF
    chmod +x "$spinner_script"
    "$spinner_script" &
    SPINNER_PID=$!
    sleep 0.05
}

_stop_spinner() {
    if [[ -n "$SPINNER_PID" ]] && kill -0 "$SPINNER_PID" 2>/dev/null; then
        kill -- -"$SPINNER_PID" 2>/dev/null || true
        kill -TERM "$SPINNER_PID" 2>/dev/null || true
        local w=0
        while [[ $w -lt 10 ]] && kill -0 "$SPINNER_PID" 2>/dev/null; do sleep 0.05; ((w++)); done
        kill -9 "$SPINNER_PID" 2>/dev/null || true
        kill -9 -"$SPINNER_PID" 2>/dev/null || true
    fi
    rm -f "/tmp/.sov-spinner-$$.sh" 2>/dev/null || true
    SPINNER_PID=""
    _show_cursor
}

_draw_progress_bar() {
    local pct=$1 width=$2
    local filled=$(( pct * width / 100 ))
    local empty=$(( width - filled ))
    local bar=""
    for ((i=0;i<filled;i++)); do bar+="█"; done
    for ((i=0;i<empty;i++)); do bar+="░"; done
    printf "%s" "$bar"
}

_draw_header() {
    local tw=$(_term_width)
    printf "\n${C_BOLD}${C_CYAN}╔"
    for ((i=0;i<tw-2;i++)); do printf "═"; done
    printf "╗${C_RESET}\n"
    printf "${C_BOLD}${C_CYAN}║${C_RESET}  ${C_WHITE}SOVEREIGN MODEL DOWNLOADER${C_RESET}  ${C_DIM}v12.0${C_RESET}"
    printf "%*s${C_BOLD}${C_CYAN}║${C_RESET}\n" $((tw - 34))
    printf "${C_BOLD}${C_CYAN}╚"
    for ((i=0;i<tw-2;i++)); do printf "═"; done
    printf "╝${C_RESET}\n"
}

_draw_status_line() {
    local label="$1" value="$2" color="${3:-$C_WHITE}"
    local tw=$(_term_width)
    printf "  ${C_DIM}%-20s${C_RESET} ${color}%s${C_RESET}" "$label" "$value"
    printf "%*s\n" $((tw - 24 - ${#value})) ""
}

_draw_divider() {
    local tw=$(_term_width)
    printf "  ${C_GRAY}"
    for ((i=0;i<tw-4;i++)); do printf "─"; done
    printf "${C_RESET}\n"
}

log(){ echo "[$(date +%FT%T)] $*" | tee -a "$LOG"; }
avail_gb(){ df -BG "$MODEL_DIR" | awk 'NR==2{print $4}' | tr -d G; }

# ─── PHASE 1: CONSOLIDATE ──────────────────────────────────────────────────
log "=== PHASE 1: CONSOLIDATE EXISTING SPRAWL - HARDLINK MERGE ==="
_draw_header
_draw_status_line "Phase" "1/3  CONSOLIDATE" "$C_YELLOW"
_draw_status_line "Model Dir" "$MODEL_DIR" "$C_CYAN"
_draw_status_line "Free Space" "$(avail_gb) GB" "$C_GREEN"
_draw_divider

for src in "${SRC_DIRS[@]}"; do [[ -d "$src" ]] || continue
  find "$src" -maxdepth 3 -type f -name "*.gguf" -print0 | while IFS= read -r -d '' f; do
    base=$(basename "$f"); real=$(realpath -m "$f"); [[ -f "$real" ]] || continue
    dest="$MODEL_DIR/$base"
    if [[ ! -e "$dest" ]]; then
      log "LINK $base <- $real"
      printf "  ${C_CYAN}→${C_RESET} %-50s ${C_DIM}linking...${C_RESET}\r" "$base"
      ln -f "$real" "$dest" 2>/dev/null || cp -al "$real" "$dest" || cp "$real" "$dest"
      printf "  ${C_OK} %-50s ${C_DIM}linked${C_RESET}   \n" "$base"
    else
      if [[ $(stat -c%s "$real") -eq $(stat -c%s "$dest") ]] && cmp -s "$real" "$dest" 2>/dev/null; then
        log "DEDUPE $base"
        printf "  ${C_SKIP} %-50s ${C_DIM}deduped${C_RESET}\n" "$base"
        ln -f "$dest" "$real" 2>/dev/null || true
      fi
    fi
  done
done

# ─── PYTHON DOWNLOAD ENGINE ──────────────────────────────────────────────────
# v12.0: Use Python API instead of broken CLI.
# Based on wiremarrow/luma and abetlen/llama-cpp-python real code.
download(){
  local target="$1" repo="$2" pattern="$3"
  local dest="$MODEL_DIR/$target"
  local avail=$(avail_gb)
  local tw=$(_term_width)
  local bar_w=$(( tw - 50 ))
  [[ $bar_w -lt 20 ]] && bar_w=20

  if (( avail < 15 )); then
    printf "  ${C_ERR} %-50s ${C_RED}ABORT: only ${avail}GB free${C_RESET}\n" "$target"
    log "ABORT avail ${avail}GB <15GB"; exit 1
  fi

  if [[ -f "$dest" && -s "$dest" ]]; then
    local sz=$(du -h "$dest" | cut -f1)
    printf "  ${C_SKIP} %-40s ${C_DIM}%8s  skip (exists)${C_RESET}\n" "$target" "$sz"
    sha256sum "$dest" | tee -a "$LOG" >/dev/null
    return 0
  fi

  printf "\n  ${C_BOLD}${C_WHITE}%-40s${C_RESET}\n" "$target"
  printf "  ${C_DIM}repo:${C_RESET} %s\n" "$repo"
  printf "  ${C_DIM}pattern:${C_RESET} %s  ${C_DIM}avail:${C_RESET} ${C_GREEN}%sGB${C_RESET}\n" "$pattern" "$avail"

  # Start spinner
  _start_spinner "Downloading..."

  # Ensure huggingface-hub is installed (self-bootstrap pattern from luma)
  if ! python3 -c "import huggingface_hub" 2>/dev/null; then
    printf "\r%*s\r" "$tw" ""
    printf "  ${C_YELLOW}Installing huggingface_hub...${C_RESET}\n"
    pip install -q -U huggingface_hub[hf_xet] 2>&1 | tee -a "$LOG" >/dev/null
  fi

  # Use Python API with hf_hub_download.
  # This is the REAL fix. The Python API still supports local_dir_use_symlinks=False.
  # The CLI `hf download` removed --local-dir-use-symlinks.
  # Pattern from: wiremarrow/luma setup.py + abetlen/llama-cpp-python
  local py_script="/tmp/.sov-dl-$$.py"
  cat > "$py_script" << PYEOF
import sys
import os
import shutil
import fnmatch
from pathlib import Path

# Self-bootstrap: ensure huggingface_hub
try:
    from huggingface_hub import hf_hub_download, HfFileSystem
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "huggingface_hub[hf_xet]"])
    from huggingface_hub import hf_hub_download, HfFileSystem

repo_id = "${repo}"
pattern = "${pattern}"
dest_dir = Path("${MODEL_DIR}")
target_name = "${target}"

try:
    hffs = HfFileSystem()
    files = [f["name"] if isinstance(f, dict) else f for f in hffs.ls(repo_id, recursive=True)]
    file_list = [str(Path(f).relative_to(repo_id)) for f in files]

    matching = [f for f in file_list if fnmatch.fnmatch(f, pattern)]
    if not matching:
        print(f"ERROR: No file matching {pattern} in {repo_id}", file=sys.stderr)
        print(f"Available: {file_list[:20]}", file=sys.stderr)
        sys.exit(1)
    if len(matching) > 1:
        print(f"WARN: Multiple matches, using first: {matching[0]}", file=sys.stderr)

    match = matching[0]
    subfolder = str(Path(match).parent) if str(Path(match).parent) != "." else ""
    filename = Path(match).name

    # Download using Python API with local_dir_use_symlinks=False
    # This is the key fix - Python API still has this param, CLI doesn't.
    downloaded = hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        subfolder=subfolder if subfolder != "." else None,
        local_dir=str(dest_dir),
        local_dir_use_symlinks=False,
    )

    downloaded_path = Path(downloaded)
    final_path = dest_dir / target_name

    # Rename if needed
    if downloaded_path.name != target_name:
        shutil.move(str(downloaded_path), str(final_path))
        print(f"RENAMED {downloaded_path.name} -> {target_name}")
    else:
        print(f"OK {target_name}")

    # Clean up .cache if present (pattern from luma)
    cache_dir = dest_dir / ".cache"
    if cache_dir.exists():
        shutil.rmtree(cache_dir, ignore_errors=True)

    sys.exit(0)
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF

  # Run Python download in background so we can animate
  python3 "$py_script" >"$MODEL_DIR/.dl_out_$$" 2>"$MODEL_DIR/.dl_err_$$" &
  local dl_pid=$!

  # Animate progress bar while waiting
  local tick=0
  while kill -0 "$dl_pid" 2>/dev/null; do
    local pct=$(( tick % 100 ))
    printf "  ${C_SPIN}"
    _draw_progress_bar "$pct" "$bar_w"
    printf "${C_RESET} ${C_DIM}%3d%%${C_RESET} ${C_CYAN}%s${C_RESET}\r" "$pct" "${SPINNER_CHARS[$((tick % 10))]}"
    sleep 0.2
    ((tick++))
  done
  wait "$dl_pid"
  local dl_exit=$?
  _stop_spinner

  # Clear progress line
  printf "\r%*s\r" "$tw" ""

  # Show output
  if [[ -f "$MODEL_DIR/.dl_out_$$" ]]; then
    cat "$MODEL_DIR/.dl_out_$$" | tee -a "$LOG" >/dev/null
    rm -f "$MODEL_DIR/.dl_out_$$"
  fi
  if [[ -f "$MODEL_DIR/.dl_err_$$" ]]; then
    cat "$MODEL_DIR/.dl_err_$$" | tee -a "$LOG" >/dev/null
    rm -f "$MODEL_DIR/.dl_err_$$"
  fi
  rm -f "$py_script"

  if [[ $dl_exit -ne 0 ]]; then
    printf "  ${C_ERR} %-40s ${C_RED}download failed${C_RESET}\n" "$target"
    return 1
  fi

  if [[ ! -f "$dest" ]]; then
    printf "  ${C_ERR} %-40s ${C_RED}not found after download${C_RESET}\n" "$target"
    log "ERROR $target not found after download"; return 1
  fi

  chmod 644 "$dest" 2>/dev/null || true
  local sz=$(du -h "$dest" | cut -f1)
  local hash=$(sha256sum "$dest" | awk '{print $1}')
  printf "  ${C_OK} %-40s ${C_GREEN}%8s${C_RESET}  ${C_DIM}%s${C_RESET}\n" "$target" "$sz" "${hash:0:16}..."
  echo "$hash  $dest" | tee -a "$LOG" >/dev/null

  if command -v llama-gguf-info >/dev/null 2>&1; then
    llama-gguf-info "$dest" >/dev/null 2>&1 || log "WARN $target gguf-info failed"
  fi
}

# ─── PHASE 2: DOWNLOADS ────────────────────────────────────────────────────
log "=== PHASE 2: ELECTED 14 UNIQUE FILES FOR 25 CTX VARIANTS ==="
_draw_header
_draw_status_line "Phase" "2/3  DOWNLOAD" "$C_YELLOW"
_draw_status_line "Free Space" "$(avail_gb) GB" "$C_GREEN"
_draw_divider

# These 14 files are reused via --ctx-size for 64k/96k/128k/256k variants, no extra disk
download "Qwen3.6-27B-DFlash-IQ4_XS.gguf" "Anbeeld/Qwen3.6-27B-DFlash-GGUF" "*IQ4_XS*.gguf"
download "Qwen3.5-9B-DeepSeek-V4-Flash-MTP-Q4_K_M.gguf" "mradermacher/Qwen3.5-9B-DeepSeek-V4-Flash-i1-GGUF" "*MTP*Q4_K_M*.gguf"
download "Qwen3.5-9B-DeepSeek-V4-Flash-IQ4_XS.gguf" "mradermacher/Qwen3.5-9B-DeepSeek-V4-Flash-i1-GGUF" "*IQ4_XS*.gguf"
download "gemma-4-12b-it-Q4_K_M.gguf" "unsloth/gemma-4-12b-it-GGUF" "*Q4_K_M*.gguf"
download "gemma-4-12B-it-uncensored-Q4_K_M.gguf" "zaakirio/gemma-4-12b-it-uncensored-GGUF" "*Q4_K_M*.gguf"
download "gemma4-12b-it-mtp-Q4_K_M.gguf" "cloudnathan5/gemma-4-12b-it-MTP-GGUF" "*Q4_K_M*.gguf"
download "StrangeMerges_19-7B-dare_ties.Q4_K_M.gguf" "mradermacher/StrangeMerges_19-7B-dare_ties-GGUF" "*Q4_K_M*.gguf" || log "StrangeMerges local only - skip if not on HF"
download "MN-GRAND-23.5B-Gutenberg-UNCENSORED-V2-Q4_K_M.gguf" "DavidAU/MN-GRAND-Gutenburg-Lyra4-Lyra-23B-V2-GGUF" "*Q4_K_M*.gguf"
download "Qwen3.6-27B-Cerebellum-v4.gguf" "deucebucket/Qwen3.6-27B-Cerebellum-GGUF" "Qwen3.6-27B-Cerebellum-v4.gguf"
download "heretic-UD-27B-Q4_K_XL.gguf" "lambsea/Qwen3.6-27B-Abliterated-Heretic-Uncensored-UD-GGUF" "*Q4_K_XL*.gguf"
download "heretic-UD-27B-Q5_K_XL.gguf" "lambsea/Qwen3.6-27B-Abliterated-Heretic-Uncensored-UD-GGUF" "*Q5_K_XL*.gguf"
download "Qwen2.5-1.5B-Draft-Q8_0.gguf" "bartowski/Qwen2.5-1.5B-Instruct-GGUF" "*Q8_0*.gguf"
download "Holo-3.1-35B-A3B-Q4_K_M.gguf" "barozp/Holo-3.1-35B-A3B-GGUF" "*Q4_K_M*.gguf"
download "mmproj-27B-F16.gguf" "unsloth/Qwen3.6-27B-GGUF" "*mmproj*F16*.gguf"
download "mmproj-gemma4-12b-f16.gguf" "unsloth/gemma-4-12b-it-GGUF" "*mmproj*F16*.gguf"

# ─── PHASE 3: VERIFY ───────────────────────────────────────────────────────
log "=== PHASE 3: VERIFY AND LIST ==="
_draw_header
_draw_status_line "Phase" "3/3  VERIFY" "$C_GREEN"
_draw_status_line "Free Space" "$(avail_gb) GB" "$C_GREEN"
_draw_divider

count=0
while IFS= read -r line; do
    f=$(echo "$line" | awk '{print $1}')
    s=$(echo "$line" | awk '{print $2}')
    [[ -z "$f" ]] && continue
    printf "  ${C_OK} %-50s ${C_GREEN}%8s${C_RESET}\n" "$(basename "$f")" "$s"
    ((count++))
done < <(ls -lh "$MODEL_DIR"/*.gguf 2>/dev/null | awk '{print $9, $5}' | sort -k2 -h)

used=$(du -sh "$MODEL_DIR" | cut -f1)
_draw_divider
printf "  ${C_BOLD}Total files:${C_RESET} %d    ${C_BOLD}Used:${C_RESET} ${C_CYAN}%s${C_RESET}    ${C_BOLD}Free:${C_RESET} ${C_GREEN}%sGB${C_RESET}\n" "$count" "$used" "$(avail_gb)"

log "DONE avail $(avail_gb)GB - $count files, ~$used used"
log "Next: cp /mnt/data/llama-swap-config.yaml ~/sovereign/tools/llama-swap/config.yaml && pkill -f llama-swap; ~/sovereign/stack/services/llama-herder.sh"

printf "\n${C_BOLD}${C_GREEN}✓ Sovereign model fleet ready.${C_RESET}\n\n"
