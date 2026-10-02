#!/bin/bash
# L4: Rust remnants — module paths, panic sites, lazy-init markers.
set -u
BIN=/opt/hatch/bin/hatch
OUT=../findings/lane4_rust.txt
{
echo "== panic location strings (top) =="
grep -a -o -E '[a-z0-9_/.-]+\.rs:[0-9]+' "$BIN" | sort | uniq -c | sort -rn | head -40
echo; echo "== hatch:: module paths =="
grep -a -o -E 'hatch::[a-z0-9_:]{3,80}' "$BIN" | sort -u | head -60
echo; echo "== compaction-adjacent strings =="
grep -a -o -E '.{0,60}compaction.{0,60}' "$BIN" | head -40
echo; echo "== lazy-init markers =="
grep -a -o -E 'OnceLock|get_or_init|lazy_static|std::env::var|env::var' "$BIN" | sort | uniq -c
echo; echo "== avocado strings =="
grep -a -o -E '.{0,50}[Aa]vocado.{0,50}' "$BIN" | head -30
} > "$OUT"
wc -l "$OUT"
