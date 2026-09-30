#!/bin/bash
cd /home/toxic/sovereign
echo "### UNTRACKED: absent from origin/main (candidates) ###"
git status --porcelain | grep "^??" | awk "{print \$2}" | while read p; do
  if ! git ls-tree origin/main -- "$p" >/dev/null 2>&1 || [ -z "$(git ls-tree origin/main -- "$p" 2>/dev/null)" ]; then
    echo "NEW: $p"
  fi
done
echo ""
echo "### TRACKED-MODIFIED: main untouched since HEAD (genuinely new local content) ###"
git status --porcelain | grep -E "^ M|^M" | awk "{print \$2}" | while read p; do
  mainblob=$(git rev-parse "origin/main:$p" 2>/dev/null || echo X)
  headblob=$(git rev-parse "HEAD:$p" 2>/dev/null || echo Y)
  workblob=$(git hash-object "$p" 2>/dev/null || echo Z)
  if [ "$mainblob" = "$headblob" ] && [ "$workblob" != "$mainblob" ]; then
    echo "FRESH: $p"
  fi
done
