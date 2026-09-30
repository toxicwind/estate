#!/bin/bash
f="$1"
rel="${f#/home/toxic/ocr-sweep/shots/}"
safe="$(echo "$rel" | tr "/" "_")"
out="/home/toxic/ocr-sweep/txt/${safe}.txt"
[ -f "$out" ] && exit 0
timeout 20 tesseract "$f" "${out%.txt}" -l eng --psm 6 >/dev/null 2>&1 || echo "FAIL $f" >> /home/toxic/ocr-sweep/ocr-fails.log
