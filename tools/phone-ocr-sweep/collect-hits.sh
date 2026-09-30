#!/bin/bash
# Collect hit images into the evidence hits dir.
# Usage: collect-hits.sh <hits-dir>
# Reads hit list from /home/toxic/ocr-sweep/hit-files.txt (one txt basename per line)
HITS_DIR="$1"
mkdir -p "$HITS_DIR"
SWEEP=/home/toxic/ocr-sweep
copied=0
while IFS= read -r t; do
  base="${t%.txt}"
  if [[ "$base" == shots_Screenshots_GJRJ_Useful_Frames_* ]]; then
    rest="${base#shots_Screenshots_GJRJ_Useful_Frames_}"
    src="$SWEEP/shots/Screenshots/GJRJ_Useful_Frames/$rest"
  elif [[ "$base" == shots_Screenshots_* ]]; then
    rest="${base#shots_Screenshots_}"
    src="$SWEEP/shots/Screenshots/$rest"
  elif [[ "$base" == shots_* ]]; then
    rest="${base#shots_}"
    src="$SWEEP/shots/$rest"
  else
    echo "UNMAPPED: $t" >> "$SWEEP/collect-warnings.log"
    continue
  fi
  if [ -f "$src" ]; then
    cp "$src" "$HITS_DIR/"
    copied=$((copied+1))
  else
    echo "NOTFOUND: $src (from $t)" >> "$SWEEP/collect-warnings.log"
  fi
done < "$SWEEP/hit-files.txt"
echo "copied=$copied"
