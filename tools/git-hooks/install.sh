#!/bin/sh
# =============================================================================
# install.sh — install hooksmith hooks into a repo's .git/hooks/.
# Usage: install.sh [path-to-repo]   (default: current directory)
#
# - Inside sovereign-projects (repo has tools/git-hooks/): symlinks, so the
#   installed hooks always match the checked-out version. Absolute target, so
#   git worktrees resolve correctly.
# - Any other repo: copies the hook scripts + gitleaks.toml as a snapshot.
#   Re-run install.sh after pulling hook updates.
#
# Idempotent: safe to re-run. Overwrites any existing pre-commit / pre-push.
# =============================================================================

set -eu

TARGET="${1:-.}"
GIT_DIR="$(git -C "$TARGET" rev-parse --git-dir 2>/dev/null)" || {
    echo "install.sh: not a git repo: $TARGET" >&2
    exit 1
}
case "$GIT_DIR" in
    /*) ;;
    *) GIT_DIR="$(CDPATH= cd -- "$TARGET" && pwd)/$GIT_DIR" ;;
esac
ROOT="$(git -C "$TARGET" rev-parse --show-toplevel)"
HOOKS="$GIT_DIR/hooks"

SRC_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

install_one() { # $1 = hook name
    name="$1"
    dest="$HOOKS/$name"
    if [ -f "$ROOT/tools/git-hooks/$name" ]; then
        # sovereign-projects layout: absolute symlink to the versioned script
        ln -sfn "$ROOT/tools/git-hooks/$name" "$dest"
        echo "install.sh: symlinked $name -> $ROOT/tools/git-hooks/$name"
    else
        cp -f "$SRC_DIR/$name" "$dest"
        echo "install.sh: copied $name (snapshot — re-run install.sh to update)"
    fi
    chmod +x "$dest"
}

mkdir -p "$HOOKS"
install_one pre-commit
install_one pre-push

# Copied installs need the config next to the hooks (symlinked installs
# resolve it via the repo's tools/git-hooks/gitleaks.toml).
if [ ! -f "$ROOT/tools/git-hooks/gitleaks.toml" ]; then
    cp -f "$SRC_DIR/gitleaks.toml" "$HOOKS/gitleaks.toml"
    echo "install.sh: copied gitleaks.toml next to hooks"
fi

echo "install.sh: done — hooks live in $HOOKS"
