#!/bin/bash
# Full OCR pass over all pulled screenshots. Idempotent: skips existing .txt.
#
# SINGLE-INSTANCE GUARD: refuses to start while another instance holds the
# lock. Added 2026-09-30 after two swarm-watchdog eject events within 40 min
# on the same corpus: yote load 84.7/105.4/82.0 @04:59 MDT (xargs -P16, yote
# lane blind, spike self-terminated ~05:10), then 49.6 @05:39 MDT (TWO -P4
# drivers stacked on the same corpus, eject shed one). Duplicates must never
# stack silently again. Keep -P4: 4 tesseract workers fit the 16-core box
# alongside herd/llama-server/squawk; -P16 tripped the interlock.
exec 9>/home/toxic/ocr-sweep/run-ocr.lock
flock -n 9 || { echo "run-ocr.sh: another instance is already running — refusing to stack (PID $$)" >&2; exit 1; }
cd /home/toxic/ocr-sweep
find shots -type f \( -iname "*.png" -o -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.webp" \) -print0 \
  | xargs -0 -P4 -n1 /home/toxic/ocr-sweep/ocr-one.sh
echo "OCR_FULL_PASS_DONE $(date -u +%FT%TZ) txt=$(ls txt/*.txt | wc -l)" >> /home/toxic/ocr-sweep/ocr-progress.log
