#!/usr/bin/env bash
# Yote deploy bundle applier — STAGE-ONLY helper, review before use.
# Default is --dry-run (prints what it WOULD do). --apply performs the copy.
# Verifies sha256 of each staged file against MANIFEST.txt before copying.
# NEVER restarts/kills any service. NEVER touches squawk.
set -euo pipefail

STAGE_DIR="$(cd "$(dirname "$0")" && pwd)"
MODE="--dry-run"
[[ "${1:-}" == "--apply" ]] && MODE="--apply"

sha256_of() { sha256sum "$1" | awk '{print $1}'; }

# Explicit per-file expectations (from MANIFEST.txt; keep in sync).
declare -A EXPECT=(
  [yote-fix.sh]="e6904f4a5843f219ffba6b207d9959f3d72b2a7edef92560fea9b8b127213f1e /home/toxic/yote-ops/yote-fix.sh"
  [yote-doctor.sh]="5dca76ee6ff39cadbe243984c0546e2051e52b6a04f8b1e3c6b3f16a35e9f495 /home/toxic/yote-ops/yote-doctor.sh"
  [awrawr_ws_exec.py]="40b282f2a0293927a42b123bc4cde3338c2e9d1dcc0e63f57bdb9ae3efabdfcd /home/toxic/sovereign/shingle-workspace/awrawr_ws_exec.py.new"
)
declare -A CHMODX=([yote-fix.sh]=1 [yote-doctor.sh]=1)  # scripts only; .py staged as .new

fail() { echo "ABORT: $*" >&2; exit 1; }

echo "=== yote deploy bundle: $MODE ==="
echo "Staged files are read from: $STAGE_DIR"

# 1. Verify checksums of everything staged before touching anything else.
for f in yote-fix.sh yote-doctor.sh awrawr_ws_exec.py; do
  [[ -f "$STAGE_DIR/$f" ]] || fail "staged file missing: $f"
  read -r want dest <<<"${EXPECT[$f]}"
  got="$(sha256_of "$STAGE_DIR/$f")"
  [[ "$got" == "$want" ]] || fail "sha256 mismatch for $f (got $got, want $want)"
  echo "OK  sha256 $f"
done

# 2. Copy (+ chmod +x the scripts). Destinations are created, never the reverse.
mkdir -p /home/toxic/yote-ops /home/toxic/sovereign/shingle-workspace
for f in yote-fix.sh yote-doctor.sh awrawr_ws_exec.py; do
  read -r _ dest <<<"${EXPECT[$f]}"
  if [[ "$MODE" == "--dry-run" ]]; then
    echo "WOULD install $STAGE_DIR/$f -> $dest${CHMODX[$f]:+ (+ chmod +x)}"
  else
    cp "$STAGE_DIR/$f" "$dest"
    [[ -n "${CHMODX[$f]:-}" ]] && chmod +x "$dest"
    echo "INSTALLED $f -> $dest"
  fi
done

if [[ "$MODE" == "--dry-run" ]]; then
  echo "DRY RUN complete — nothing was copied. Re-run with --apply to install."
fi
echo
echo "=== post-apply verification checklist (VERIFY.md) ==="
cat "$STAGE_DIR/VERIFY.md"
