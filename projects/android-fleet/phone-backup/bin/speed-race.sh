#!/usr/bin/env bash
# speed-race.sh — hyper-race Android bulk transfer methods, keep the winner.
# Runs on yote (has adb). Usage: speed-race.sh [results-dir]
set -u
RESULTS="${1:-/tmp/speed-race}"
mkdir -p "$RESULTS"

PIXEL="${PIXEL:-}"
if [[ -z "$PIXEL" ]]; then
  PIXEL="$(adb devices | awk '/^10\.0\.0\.77:[0-9]+[[:space:]]+device/{print $1; exit}')"
fi
[[ -n "$PIXEL" ]] || { echo "no pixel endpoint"; exit 1; }
export PIXEL
echo "pixel=$PIXEL"

A() { adb -s "$PIXEL" "$@"; }
export -f A

# ---- build test payloads (idempotent) ----
echo "== building payloads =="
A shell 'mkdir -p /sdcard/bench-small /sdcard/bench-big' >/dev/null
# 1000 x 100KB textish files (small-file torture)
A shell 'ls /sdcard/bench-small | wc -l' | grep -q '^1000$' || \
  A shell 'for i in $(seq 1 1000); do head -c 102400 /dev/urandom | base64 > /sdcard/bench-small/f$(printf %04d $i).txt; done'
# 1 x 300MB incompressible blob (sequential throughput)
A shell 'ls -l /sdcard/bench-big/blob.bin 2>/dev/null | grep -q " 314572800 " || echo MISSING' | grep -q MISSING && \
  A shell 'head -c 314572800 /dev/urandom > /sdcard/bench-big/blob.bin'
echo "payloads ready"

run() { # name, command...
  local name="$1"; shift
  local dest="$RESULTS/$name"; rm -rf "$dest"; mkdir -p "$dest"
  echo "== race: $name =="
  local t0 t1 dt
  t0=$(date +%s.%N)
  "$@" "$dest"
  t1=$(date +%s.%N)
  dt=$(echo "$t1 - $t0" | bc)
  local bytes; bytes=$(du -sb "$dest" | cut -f1)
  local mbps; mbps=$(echo "scale=1; $bytes / $dt / 1048576" | bc)
  printf '%-28s %8.1fs %8s MB %6s MB/s\n' "$name" "$dt" "$((bytes/1048576))" "$mbps" | tee -a "$RESULTS/RESULTS.txt"
}

: > "$RESULTS/RESULTS.txt"
echo "== $(date -u +%FT%TZ) pixel=$PIXEL ==" | tee -a "$RESULTS/RESULTS.txt"

# 1. baseline: plain adb pull, small files
run pull-1way-small  bash -c 'A pull /sdcard/bench-small "$0" >/dev/null 2>&1'
# 2. parallel by file batches (8-way)
run pull-8way-small bash -c '
  dest="$0"
  A shell "ls /sdcard/bench-small" | tr -d "\r" | \
    xargs -P8 -n125 -I{} sh -c "adb -s \"$PIXEL\" pull /sdcard/bench-small/{} \"$dest/{}\" >/dev/null 2>&1"'
# 3. on-device tar, then single pull (small files -> one stream)
run tardev-pull-small bash -c '
  dest="$0"
  A shell "tar -cf /sdcard/bench-small.tar -C /sdcard bench-small" >/dev/null 2>&1
  A pull /sdcard/bench-small.tar "$dest/small.tar" >/dev/null 2>&1
  A shell "rm /sdcard/bench-small.tar" >/dev/null 2>&1'
# 4. baseline: plain adb pull, big blob
run pull-1way-big   bash -c 'A pull /sdcard/bench-big "$0" >/dev/null 2>&1'
# 5. on-device tar (big blob, measures tar overhead on sequential)
run tardev-pull-big  bash -c '
  dest="$0"
  A shell "tar -cf /sdcard/bench-big.tar -C /sdcard bench-big" >/dev/null 2>&1
  A pull /sdcard/bench-big.tar "$dest/big.tar" >/dev/null 2>&1
  A shell "rm /sdcard/bench-big.tar" >/dev/null 2>&1'
# 6. adb pull -z (compressed transport), big blob
run pull-z-big      bash -c 'A pull -z any /sdcard/bench-big "$0" >/dev/null 2>&1'
# 7. adb pull -z, small files
run pull-z-small    bash -c 'A pull -z any /sdcard/bench-small "$0" >/dev/null 2>&1'
# 8. exec-out cat pipe, big blob (skips sync-protocol round trips)
run catpipe-big     bash -c 'A exec-out "cat /sdcard/bench-big/blob.bin" > "$0/blob.bin" 2>/dev/null'

echo; echo "===== RESULTS ====="; cat "$RESULTS/RESULTS.txt"
