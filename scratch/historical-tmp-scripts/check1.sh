#!/bin/bash
cd /home/toxic/sovereign
echo "=== patches on origin/main ==="
git ls-tree origin/main --name-only -- projects/tau/upstream-changes/patches/ | head -10
echo "=== patch count/size on main ==="
git ls-tree -r -l origin/main -- projects/tau/upstream-changes/patches/ | awk "{s+=\$4; n++} END {print n\" files,\"s\" bytes\"}"
echo "=== secret scan new files ==="
grep -rniE "sk-[a-zA-Z0-9]{16,}|ghp_[a-zA-Z0-9]{20,}|xox[bap]-|AKIA[0-9A-Z]{16}" ops/nginx/nginx.conf projects/bridge/bin/bg-ctl.py projects/openrouter-probe/e2e-probe.py projects/openrouter-probe/rewire_peer_v3.py projects/mesh/bin/landing.py projects/tau/upstream-changes/scripts/ingest.sh projects/yote/PLAN.md 2>/dev/null | head -5
echo SCAN_DONE
