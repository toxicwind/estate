#!/usr/bin/env bash
set -uo pipefail

SK_DIR="/home/toxic/sovereign/skills"
PASS=0; FAIL=0; MISSING=0

echo "=== Frontmatter Audit: $(date -u +%FT%TZ) ==="
echo ""

# Single-pass: find all SKILL.md files and check frontmatter
while IFS= read -r f; do
  name_line=$(head -15 "$f" | /usr/bin/rg -i '^name:' 2>/dev/null || true)
  desc_line=$(head -30 "$f" | /usr/bin/rg -i '^description:' 2>/dev/null || true)
  
  if [ -z "$name_line" ]; then
    echo "FAIL: $f — missing name:"
    FAIL=$((FAIL+1))
  elif [ -z "$desc_line" ]; then
    echo "FAIL: $f — missing description:"
    FAIL=$((FAIL+1))
  else
    name_val=$(echo "$name_line" | sed 's/^name: *//')
    echo "PASS: $f — name=$name_val"
    PASS=$((PASS+1))
  fi
done < <(find "$SK_DIR" -name "SKILL.md" -not -path "*/node_modules/*" -not -path "*/.github/*" 2>/dev/null | sort)

echo ""
echo "=== Result: $PASS pass, $FAIL fail ==="
[ "$FAIL" -eq 0 ]
