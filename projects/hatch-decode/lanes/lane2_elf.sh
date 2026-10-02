#!/bin/bash
# L2: ELF/dynamic structure.
set -u
BIN=/opt/hatch/bin/hatch
OUT=../findings/lane2_elf.txt
{
echo "== sections =="; readelf -S -W "$BIN" | head -50
echo; echo "== dynamic =="; readelf -d -W "$BIN"
echo; echo "== build-id =="; readelf -n "$BIN" | head -6
echo; echo "== .rustc section? =="; readelf -S -W "$BIN" | grep -i rustc || echo none
echo; echo "== linked libs =="; ldd "$BIN"
} > "$OUT"
wc -l "$OUT"
