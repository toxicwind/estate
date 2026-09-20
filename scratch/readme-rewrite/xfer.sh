#!/bin/bash
# Transfer local README files to the awrawr-pc worktree via chunked base64.
# Usage: xfer.sh <src1> <dst1> [<src2> <dst2> ...]   (dst = repo-relative path)
set -u
cd ~/workspace/skills/awrawr-mcp || exit 1
WT=/home/toxic/readme-wt-monorepo

xfer() {
  local src="$1" dst="$2"
  local b64 len i first chunk op out
  b64=$(base64 -w0 "$src") || { echo "FAIL b64 $src"; return 1; }
  len=${#b64}
  i=0
  first=1
  while [ "$i" -lt "$len" ]; do
    chunk=${b64:$i:3000}
    op=">>"
    if [ "$first" -eq 1 ]; then op=">"; fi
    out=$(python3 bin/exec.py "printf '%s' '$chunk' | base64 -d $op '$WT/$dst'" 2>&1) || { echo "FAIL xfer $dst @ $i: $out"; return 1; }
    first=0
    i=$((i+3000))
  done
  echo "SENT $dst"
}

while [ $# -ge 2 ]; do
  xfer "$1" "$2" || exit 1
  shift 2
done
echo "ALL SENT"
