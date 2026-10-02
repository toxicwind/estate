#!/usr/bin/env bash
# Frontmatter audit for SKILL.md files against the SkillFrontmatter spec.
# Usage: bash frontmatter-audit.sh [skills_dir]
# Default skills_dir: the skills/ dir of the repo this script lives in.
# Validates: frontmatter block exists; name unquoted, lowercase-hyphenated,
# matches directory name; description present and >= 20 chars.
# Exit 0 only when every file passes.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SK_DIR="${1:-$(cd "$SCRIPT_DIR/.." && pwd)}"

PASS=0; FAIL=0; TOTAL=0

echo "=== Frontmatter Audit: $(date -u +%FT%TZ) ==="
echo "=== skills dir: $SK_DIR ==="
echo ""

while IFS= read -r f; do
  TOTAL=$((TOTAL+1))
  rel="${f#$SK_DIR/}"
  dir="$(basename "$(dirname "$f")")"
  problems=""

  # frontmatter block: first line ---, closed by a later ---
  first="$(head -1 "$f")"
  if [ "$first" != "---" ]; then
    problems="${problems} no frontmatter block;"
  else
    block="$(awk 'NR>1 && /^\s*---\s*$/ {exit} NR>1 {print}' "$f" | head -20)"
    name_line="$(printf '%s\n' "$block" | grep -i '^name:' | head -1 || true)"
    desc_line="$(printf '%s\n' "$block" | grep -i '^description:' | head -1 || true)"
    if [ -z "$name_line" ]; then
      problems="${problems} missing name:;"
    else
      name_val="$(printf '%s' "$name_line" | sed 's/^[Nn][Aa][Mm][Ee]: *//')"
      case "$name_val" in
        \"*\"|\'*\') problems="${problems} name is quoted: $name_val;" ;;
      esac
      clean="$(printf '%s' "$name_val" | tr -d "\"'")"
      case "$clean" in
        *_*) problems="${problems} name has underscore: $clean;" ;;
      esac
      if [ "$clean" != "$(printf '%s' "$clean" | tr '[:upper:]' '[:lower:]')" ]; then
        problems="${problems} name not lowercase: $clean;"
      fi
      case "$clean" in
        *[!a-z0-9-]*|"") problems="${problems} name not lowercase-hyphenated: $clean;" ;;
      esac
      if [ "$clean" != "$dir" ]; then
        problems="${problems} name '$clean' != directory '$dir';"
      fi
    fi
    if [ -z "$desc_line" ]; then
      problems="${problems} missing description:;"
    else
      desc_val="$(printf '%s' "$desc_line" | sed 's/^[Dd][Ee][Ss][Cc][Rr][Ii][Pp][Tt][Ii][Oo][Nn]: *[>|-]* *//')"
      if [ "${#desc_val}" -lt 20 ]; then
        problems="${problems} description too short (${#desc_val} chars);"
      fi
    fi
  fi

  if [ -z "$problems" ]; then
    PASS=$((PASS+1))
  else
    FAIL=$((FAIL+1))
    echo "FAIL: $rel"
    printf '%s\n' "$problems" | tr ';' '\n' | sed '/^$/d' | sed 's/^/      -/'
  fi
done < <(find "$SK_DIR" -name "SKILL.md" -not -path "*/node_modules/*" -not -path "*/.github/*" 2>/dev/null | sort)

echo ""
echo "=== Result: $PASS pass, $FAIL fail, $TOTAL total ==="
[ "$FAIL" -eq 0 ]
