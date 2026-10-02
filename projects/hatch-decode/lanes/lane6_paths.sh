#!/bin/bash
# L6: path-constant sweep — every baked-in /etc /run /opt /var path.
set -u
BIN=/opt/hatch/bin/hatch
OUT=../findings/lane6_paths.txt
grep -a -o -E '/(etc|run|opt|var|home|root|tmp)/[A-Za-z0-9_./-]{2,90}' "$BIN" \
  | sort | uniq -c | sort -rn > "$OUT"
wc -l "$OUT"
head -60 "$OUT"
