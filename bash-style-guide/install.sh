#!/usr/bin/env bash
# ---
# install.sh - copy bashrc to ~/.bashrc and replace the current shell.
# ---

set -o errexit
set -o nounset
set -o pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="$HOME/.bashrc"
BACKUP="$HOME/.bashrc.bak.$(date +%s)"

cp -a "$TARGET" "$BACKUP" 2>/dev/null || true
cp -a "$HERE/bashrc" "$TARGET"

rm -f "$HOME/.bash-evalcache"/*.tmp "$HOME/.bash-evalcache"/*.tmp.* \
      "$HOME/.bash-evalcache"/*.lock 2>/dev/null

if ! bash -n "$TARGET"; then
  echo "SYNTAX ERROR - restoring backup."
  cp -a "$BACKUP" "$TARGET"
  exit 1
fi

echo "installed: $TARGET (backup: $BACKUP)"
exec bash --login
