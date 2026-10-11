#!/usr/bin/env bash
# runner for zipfs-vault: prefers the shared skills venv, falls back to system python3
set -euo pipefail
D="$(cd "$(dirname "$0")" && pwd)"
if [ -x "$HOME/workspace/skills/.venv/bin/python" ]; then
  exec "$HOME/workspace/skills/.venv/bin/python" "$D/main.py" "$@"
else
  exec python3 "$D/main.py" "$@"
fi
