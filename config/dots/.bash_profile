[ -f "$HOME/.bashrc" ] && . "$HOME/.bashrc"

# Load universal environment
[ -f "$HOME/.bashrc.env" ] && . "$HOME/.bashrc.env"

# 2-second rule: every non-interactive bash (agent tool shells) auto-loads the shim.
# 2026-10-19: path was ranch/two-sec/shim.sh (dead since the shim moved) — bash
# silently ignored it, so non-interactive shells lost the 2s rule entirely.
export BASH_ENV=/home/toxic/estate/bin/bash-2s-shim.sh
