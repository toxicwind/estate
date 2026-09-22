#!/bin/bash
set -e
SRC=/home/toxic/sovereign
DST=/tmp/sp-salvage
rm -rf "$DST"
git clone -q https://github.com/toxicwind/sovereign-projects.git "$DST" 2>&1 | tail -1
cd "$DST"
git checkout -q main
git fetch -q origin
git reset -q --hard origin/main
BASE=$(git rev-parse --short origin/main)
echo "BASE=$BASE"
FILES="projects/mesh/bin/landing.py projects/tau/engine/packages/coding-agent/src/cli/startup-cwd.ts projects/tau/upstream-changes/scripts/ingest.sh projects/yote/PLAN.md ops/nginx/nginx.conf projects/bridge/bin/bg-ctl.py projects/openrouter-probe/e2e-probe.py projects/openrouter-probe/rewire_peer_v3.py"
for f in $FILES; do
  mkdir -p "$(dirname "$f")"
  cp "$SRC/$f" "$f"
  git add "$f"
done
echo "=== staged ==="
git status --porcelain
