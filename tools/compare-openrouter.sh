#!/usr/bin/env bash
# OpenRouter Code Comparison Script
# Uses ast-grep for structural search across Zed, Grok, Pi, Kimi codebases

set -euo pipefail

ZED_ROOT="/home/toxic/projects/zed"
GROK_ROOT="/home/toxic/.grok"
PI_ROOT="/home/toxic/projects/pi-agent"
KIMI_ROOT="/home/toxic/projects/kimi-code-sovereign"
AST_GREP="/home/toxic/.local/share/mise/shims/ast-grep"

PATTERN="${1:-openrouter}"
LANG="${2:-typescript}"

compare_codebase() {
    local name="$1"
    local root="$2"
    local pattern="$3"
    local lang="$4"
    
    if [[ ! -d "$root" ]]; then
        echo "[$name] SKIP: directory not found at $root"
        return
    fi
    
    echo "=== [$name] ==="
    $AST_GREP scan --inline-rules "id: find-openrouter
language: $lang
rule:
  pattern: '$pattern'" "$root" 2>&1 | head -80
    echo ""
}

echo "=== OpenRouter Code Comparison ==="
echo "Pattern: $PATTERN"
echo "Language: $LANG"
echo ""

# Zed uses Rust - search for open_router module pattern
compare_codebase "ZED" "$ZED_ROOT" "open_router" "rust"
# Pi uses TypeScript
compare_codebase "PI" "$PI_ROOT" "$PATTERN" "typescript"
# Kimi uses TypeScript
compare_codebase "KIMI" "$KIMI_ROOT" "$PATTERN" "typescript"
# Grok uses TypeScript
compare_codebase "GROK" "$GROK_ROOT" "$PATTERN" "typescript"

echo "=== Done ==="