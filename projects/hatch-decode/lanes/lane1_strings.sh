#!/bin/bash
# L1: strings-context mining — one pass over the binary, context around every JARVIS_* hit.
set -u
BIN=/opt/hatch/bin/hatch
OUT=../findings/lane1_context.txt
VARS=../findings/jarvis_vars.txt
strings -a "$BIN" | grep -oE 'JARVIS_[A-Z_0-9]+' | sort -u > "$VARS"
echo "vars: $(wc -l < "$VARS")"
# single pass: every occurrence with +-context
grep -a -o -E '.{0,80}JARVIS_[A-Z_0-9]+.{0,120}' "$BIN" > "$OUT"
echo "context lines: $(wc -l < "$OUT")"
