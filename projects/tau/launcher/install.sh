#!/usr/bin/env bash
# Install (or reinstall) the tau launcher from this canonical repo copy.
#   ./install.sh [--prefix DIR]   (default prefix: $HOME/.local)
# Copies tau, tau-audit.sh, tau-tmux.sh. Idempotent.
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)"
PREFIX="${1:-$HOME/.local}"
case "${1:-}" in --prefix) PREFIX="${2:-$HOME/.local}";; esac
BIN="$PREFIX/bin"
mkdir -p "$BIN"
for f in tau tau-audit.sh tau-tmux.sh; do
  install -m 0755 "$SRC/$f" "$BIN/$f"
done
echo "installed: $BIN/tau $BIN/tau-audit.sh $BIN/tau-tmux.sh"
"$BIN/tau" audit 2>&1 | tail -3
