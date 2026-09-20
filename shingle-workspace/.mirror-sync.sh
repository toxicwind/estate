#!/bin/bash
# .mirror-sync.sh — cell ~/workspace -> /home/toxic/sovereign/shingle-workspace
# Method: tar (with regenerable-bulk excludes) -> base64 -> 118KB pieces ->
#   awrawr-mcp exec.py printf-append -> bridge reassemble + sha256 verify -> unpack.
# Transport ceiling (measured 2026-09-14): the bridge serializes large commands
# at ~2.5 calls/s; each call carries max ~88KB binary (128KB MAX_ARG_STRLEN).
# Effective throughput ~220KB/s. Do NOT try 8MB single-call chunks — E2BIG.
# gws/Drive route is dead in current cells (empty stub); rclone pull needs re-auth.
#
# Usage (run from the CELL):
#   1. Build tar:
#      cd ~/workspace && tar -czf /tmp/mirror.tar.gz \
#        --exclude=node_modules --exclude=__pycache__ --exclude='*.pyc' \
#        --exclude=.venv --exclude='chrome-headless-shell-151.zip' \
#        --exclude=externals \
#        [--exclude=./tauwork --exclude=./tau-lockregen --exclude=./runners ...] .
#   2. Upload pieces (see send_final.py pattern, kept with the run logs):
#      base64 -w0 mirror.tar.gz | split into 118000-char pieces pNNNNN
#      for each piece: exec.py "printf '%s' '<piece>' > /home/toxic/.mirror-in/pNNNNN"
#      (piece files are idempotent: re-running overwrites, safe to resume)
#   3. Assemble + verify on bridge:
#      exec.py 'cat /home/toxic/.mirror-in/p????? | base64 -d > /home/toxic/.mirror-in/mirror.tar.gz \
#        && sha256sum /home/toxic/.mirror-in/mirror.tar.gz'   # compare with local
#      exec.py 'tar -tzf /home/toxic/.mirror-in/mirror.tar.gz > /dev/null && echo TAROK'
#   4. Unpack (ADDITIVE — never touch /home/toxic/workspace, never overwrite sovereign/):
#      exec.py 'tar -xzf /home/toxic/.mirror-in/mirror.tar.gz -C /home/toxic/sovereign/shingle-workspace'
#   5. Verify: compare `find <dir> -type f | wc -l` and `du -sb` cell-vs-bridge.
#
# Safety: additive only. /home/toxic/workspace is a DIFFERENT repo
# (toxicwind/local-work-archive) — never write there. Never overwrite existing
# files under /home/toxic/sovereign/.
#
# PROPOSAL (not installed): run deltas via cron on the cell, e.g.
#   hatch-cron: 0 4 * * * : /home/toxic/sovereign/shingle-workspace/.mirror-sync.sh --delta
# --delta would rsync-style diff (tar --newer) and ship only changed files.
# Needs Chris's approval before installing any schedule.
echo "See header comments for the mirror method. Nothing executed."
