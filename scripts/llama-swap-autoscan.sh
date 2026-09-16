#!/usr/bin/env bash
# llama-swap Autoscan - Dynamic model discovery and configuration generation
# Scans for GGUF models in ~/projects/models and HF cache, generates llama-swap config.yaml

set -euo pipefail

# Configuration
MODELS_DIR="/home/toxic/projects/models"
HF_CACHE_DIR="/home/toxic/.cache/huggingface/hub"
CONFIG_TEMPLATE="/home/toxic/sovereign/tools/llama-swap/config.yaml"
CONFIG_OUTPUT="/home/toxic/sovereign/tools/llama-swap/config.yaml"
AUTOSCAN_STATE="/home/toxic/.local/share/llama-swap/autoscan-state.json"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[autoscan]${NC} $*"; }
warn() { echo -e "${YELLOW}[autoscan]${NC} $*"; }
error() { echo -e "${RED}[autoscan]${NC} $*"; }
info() { echo -e "${BLUE}[autoscan]${NC} $*"; }

# Check if file is a vision projector (mmproj) - skip these
is_mmproj() {
    local filename="$1"
    [[ "$filename" =~ ^mmproj ]] || [[ "$filename" =~ mmproj.*\.gguf$ ]]
}

# Determine fork based on model characteristics and available forks
determine_fork() {
    local filename="$1"
    local path="$2"
    
    if [[ "$path" == *"/llama-cpp-turboquant/"* ]]; then echo "turboquant"; return; fi
    if [[ "$path" == *"/ik_llama.cpp-main/"* ]]; then echo "ik_llama"; return; fi
    if [[ "$path" == *"/ik_turboquant/"* ]]; then echo "ik_turboquant"; return; fi
    
    if [[ "$filename" =~ turboquant ]] || [[ "$filename" =~ -tcq ]] || [[ "$filename" =~ turbo3 ]]; then
        echo "turboquant"
        return
    fi
    
    if [[ "$filename" =~ ik_llama ]] || [[ "$filename" =~ -fit ]]; then
        echo "ik_llama"
        return
    fi
    
    if [[ "$filename" =~ ik_turboquant ]] || [[ "$filename" =~ -tcq.*fit ]]; then
        echo "ik_turboquant"
        return
    fi
    
    echo "beellama"
}

# Determine quantization from filename
determine_quant() {
    local filename="$1"
    if [[ "$filename" =~ IQ4_XS ]]; then echo "IQ4_XS"; return; fi
    if [[ "$filename" =~ Q4_K_XL ]]; then echo "Q4_K_XL"; return; fi
    if [[ "$filename" =~ Q5_K_XL ]]; then echo "Q5_K_XL"; return; fi
    if [[ "$filename" =~ Q4_K_M ]]; then echo "Q4_K_M"; return; fi
    if [[ "$filename" =~ Q5_K_M ]]; then echo "Q5_K_M"; return; fi
    if [[ "$filename" =~ Q6_K ]]; then echo "Q6_K"; return; fi
    if [[ "$filename" =~ Q8_0 ]]; then echo "Q8_0"; return; fi
    if [[ "$filename" =~ BF16 ]]; then echo "BF16"; return; fi
    if [[ "$filename" =~ Q4_K_S ]]; then echo "Q4_K_S"; return; fi
    echo "Q4_K_M"
}

# Determine context from filename
determine_context() {
    local filename="$1"
    if [[ "$filename" =~ 256[kK] ]]; then echo 262144; return; fi
    if [[ "$filename" =~ 128[kK] ]]; then echo 131072; return; fi
    if [[ "$filename" =~ 96[kK] ]]; then echo 98304; return; fi
    if [[ "$filename" =~ 64[kK] ]]; then echo 65536; return; fi
    if [[ "$filename" =~ 32[kK] ]]; then echo 32768; return; fi
    echo 32768
}

# Determine context macro name
context_macro() {
    local ctx="$1"
    case $ctx in
        32768) echo '${CTX_32K}' ;;
        65536) echo '${CTX_64K}' ;;
        98304) echo '${CTX_96K}' ;;
        131072) echo '${CTX_128K}' ;;
        163840) echo '${CTX_160K}' ;;
        262144) echo '${CTX_256K}' ;;
        *) echo '${CTX_32K}' ;;
    esac
}

# Determine KV cache macro based on fork
kv_macro_for_fork() {
    local fork="$1"
    case "$fork" in
        "turboquant"|"ik_turboquant") echo '${KV_TURBO3}' ;;
        *) echo '${KV_Q8}' ;;
    esac
}

# Generate model ID from filename
generate_model_id() {
    local filename="$1"
    basename "$filename" .gguf | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9._-]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//'
}

# Estimate VRAM in GB
estimate_vram_gb() {
    local size="$1"
    echo $(( (size * 12 / 10) / 1024 / 1024 / 1024 + 1 ))
}

# Generate metadata YAML
generate_metadata_yaml() {
    local metadata_json="$1"
    local indent="$2"
    
    echo "$metadata_json" | jq -r 'to_entries[] | "\(.key): \(.value)"' | sed "s/^/${indent}/"
}

# Discover GGUF files and their metadata
discover_models() {
    local models_json="[]"
    declare -A seen_paths
    
    while IFS= read -r -d '' gguf; do
        if [[ -f "$gguf" || -L "$gguf" ]]; then
            local resolved=$(readlink -f "$gguf")
            local filename=$(basename "$gguf")
            
            if is_mmproj "$filename"; then
                continue
            fi
            
            if [[ -n "${seen_paths[$resolved]:-}" ]]; then
                continue
            fi
            seen_paths[$resolved]=1
            
            local size=$(stat -c%s "$resolved" 2>/dev/null || echo 0)
            if [[ $size -lt 10000000 ]]; then
                continue
            fi
            
            local model_id=$(generate_model_id "$filename")
            local fork=$(determine_fork "$filename" "$resolved")
            local quant=$(determine_quant "$filename")
            local context=$(determine_context "$filename")
            local vram_gb=$(estimate_vram_gb "$size")
            
            local origin=""
            if [[ "$resolved" == *"/repos/"* ]]; then
                origin=$(echo "$resolved" | sed 's/.*\/repos\///' | sed 's/\/.*//' | sed 's/--/\//g')
            fi
            
            local metadata="{}"
            if [[ -n "$origin" ]]; then
                metadata=$(jq -n --arg origin "$origin" '{origin: $origin}')
            fi
            
            local entry=$(cat <<EOJ
{
  "id": "$model_id",
  "fork": "$fork",
  "path": "$resolved",
  "filename": "$filename",
  "size": $size,
  "quant": "$quant",
  "context": $context,
  "vram_gb": $vram_gb,
  "metadata": $metadata
}
EOJ
)
            models_json=$(echo "$models_json" | jq --argjson entry "$entry" '. + [$entry]')
        fi
    done < <(find "$MODELS_DIR" -name "*.gguf" -print0 2>/dev/null)
    
    while IFS= read -r -d '' blob; do
        if [[ -f "$blob" ]]; then
            local size=$(stat -c%s "$blob" 2>/dev/null || echo 0)
            if [[ $size -gt 100000000 ]]; then
                local repo_path=$(dirname "$(dirname "$(dirname "$blob")")")
                local repo_name=$(basename "$repo_path")
                local repo_id=$(echo "$repo_name" | sed 's/^models--//' | sed 's/--/\//g')
                local filename=$(basename "$blob")
                local model_id=$(generate_model_id "$filename")
                
                if [[ -n "${seen_paths[$blob]:-}" ]]; then
                    continue
                fi
                
                if is_mmproj "$filename"; then
                    continue
                fi
                
                local fork=$(determine_fork "$filename" "$blob")
                local quant=$(determine_quant "$filename")
                local context=$(determine_context "$filename")
                local vram_gb=$(estimate_vram_gb "$size")
                
                local metadata=$(jq -n --arg origin "$repo_id" '{origin: $origin, hf_cache: true}')
                
                local entry=$(cat <<EOJ
{
  "id": "$model_id",
  "fork": "$fork",
  "path": "$blob",
  "filename": "$filename",
  "size": $size,
  "quant": "$quant",
  "context": $context,
  "vram_gb": $vram_gb,
  "metadata": $metadata
}
EOJ
)
                models_json=$(echo "$models_json" | jq --argjson entry "$entry" '. + [$entry]')
                seen_paths[$blob]=1
            fi
        fi
    done < <(find "$HF_CACHE_DIR" -path "*/blobs/*" -type f -print0 2>/dev/null)
    
    echo "$models_json"
}

# Generate model config entries
generate_model_config() {
    local models_json="$1"
    
    echo "$models_json" | jq -c '.[]' | while IFS= read -r model; do
        local id=$(echo "$model" | jq -r '.id')
        local fork=$(echo "$model" | jq -r '.fork')
        local path=$(echo "$model" | jq -r '.path')
        local quant=$(echo "$model" | jq -r '.quant')
        local context=$(echo "$model" | jq -r '.context')
        local vram_gb=$(echo "$model" | jq -r '.vram_gb')
        local metadata=$(echo "$model" | jq -c '.metadata')
        
        local bin_var=""
        local ld_var=""
        local fork_flags=""
        local gpu_layers=""
        local srv_base=""
        
        case "$fork" in
            "beellama")
                bin_var="\${BEELLAMA_BIN}"
                ld_var="\${BEELLAMA_LD}"
                fork_flags="\${FORK_BEELLAMA}"
                gpu_layers="\${SRV_GPU_LAYERS}"
                srv_base="\${SRV_BASE}"
                ;;
            "turboquant")
                bin_var="\${TURBO_BIN}"
                ld_var="\${TURBO_LD}"
                fork_flags="\${FORK_TURBO}"
                gpu_layers="\${SRV_GPU_LAYERS}"
                srv_base="\${SRV_BASE}"
                ;;
            "ik_llama")
                bin_var="\${IK_BIN}"
                ld_var="\${IK_LD}"
                fork_flags="\${FORK_IK}"
                gpu_layers="\${IK_GPU_LAYERS}"
                srv_base="\${SRV_IK_BASE}"
                ;;
            "ik_turboquant")
                bin_var="\${IK_TQ_BIN}"
                ld_var="\${IK_TQ_LD}"
                fork_flags="\${FORK_IK}"
                gpu_layers="\${IK_GPU_LAYERS}"
                srv_base="\${SRV_IKTQ_BASE}"
                ;;
        esac
        
        local ctx_macro=$(context_macro "$context")
        local kv_macro=$(kv_macro_for_fork "$fork")
        local metadata_yaml=$(generate_metadata_yaml "$metadata" "      ")
        
        cat <<EOY
  $id:
    cmd: $bin_var --model $path $srv_base $fork_flags $ctx_macro $kv_macro \${REASONING_OFF} \${SPEC_NONE}
    env:
      - LD_LIBRARY_PATH=$ld_var
      - \${CUDA_ENV}
      - LLAMA_API_KEY=
    name: "$(echo "$id" | sed 's/-/ /g' | sed 's/\./ /g' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) substr($i,2)} 1') · $context · $quant"
    description: "Auto-discovered model from $path"
    metadata:
      fork: $fork
      context: $context
      quant: $quant
      vram: ~${vram_gb}GB
      auto_discovered: true
      path: "$path"
$metadata_yaml

EOY
    done
}

# Main
main() {
    log "Starting llama-swap autoscan..."
    
    mkdir -p "$(dirname "$AUTOSCAN_STATE")"
    
    log "Discovering models in $MODELS_DIR and $HF_CACHE_DIR..."
    local models_json=$(discover_models)
    local model_count=$(echo "$models_json" | jq 'length')
    log "Found $model_count models"
    
    if [[ $model_count -eq 0 ]]; then
        warn "No models found! Exiting."
        exit 1
    fi
    
    log "Generating model configuration..."
    local model_config=$(generate_model_config "$models_json")
    
    log "Writing config to $CONFIG_OUTPUT..."
    
    # Write model_config to temp file
    local model_config_file=$(mktemp)
    echo "$model_config" > "$model_config_file"
    
    # Use Python to properly replace the models section using boundary marker
    python3 -c "
import sys
import os

model_config_file = '$model_config_file'
config_template = '$CONFIG_TEMPLATE'
config_output = '$CONFIG_OUTPUT'

with open(model_config_file, 'r') as f:
    model_config = f.read()

with open(config_template, 'r') as f:
    lines = f.readlines()

# Find the models: line and the AUTOSCAN_BOUNDARY comment line
models_start = None
models_end = None
for i, line in enumerate(lines):
    if line.strip() == 'models:' and models_start is None:
        models_start = i
    if models_start is not None and models_end is None:
        if 'AUTOSCAN_BOUNDARY' in line:
            models_end = i
            break

if models_start is None or models_end is None:
    print('ERROR: Could not find models section boundaries', file=sys.stderr)
    sys.exit(1)

# Build new config
new_lines = lines[:models_start + 1]  # Keep everything up to and including 'models:'
new_lines.append(model_config)  # Add generated models
new_lines.extend(lines[models_end:])  # Add everything from AUTOSCAN_BOUNDARY onwards

with open(config_output, 'w') as f:
    f.writelines(new_lines)

print('Config written successfully')
"
    
    rm -f "$model_config_file"
    
    # Save state
    echo "$models_json" | jq '{timestamp: now | todateiso8601, models: .}' > "$AUTOSCAN_STATE"
    
    log "Autoscan complete! Config written to $CONFIG_OUTPUT"
    log "Run 'llama-swap -config $CONFIG_OUTPUT -watch-config' to start"
}

main "$@"
