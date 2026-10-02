#!/bin/bash
cd /home/toxic/sovereign
echo "=== modified/deleted-tracked files with content NOT in origin/main ==="
git status --porcelain | while read st p; do
  case "$st" in
    " M"|M*|D*|" D") ;;  # tracked changed
    "??") continue ;;     # handle untracked separately
    *) continue ;;
  esac
  # working blob vs origin/main blob
  if [ "$st" = " D" ] || [[ "$st" == D* ]]; then
    workblob="DELETED"
  else
    workblob=$(git hash-object "$p" 2>/dev/null || echo MISSING)
  fi
  mainblob=$(git rev-parse "origin/main:$p" 2>/dev/null || echo NOTINMAIN)
  headblob=$(git rev-parse "HEAD:$p" 2>/dev/null || echo NOTINHEAD)
  if [ "$workblob" != "$mainblob" ] && [ "$workblob" != "$headblob" ]; then
    echo "UNIQUE  $st $p"
  fi
done
