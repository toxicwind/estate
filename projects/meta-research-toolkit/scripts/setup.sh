#!/usr/bin/env bash
set -euo pipefail

echo "[setup] Initializing meta-research-toolkit..."

# Python
python3 -m venv .venv || true
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Git submodules (if git is present)
if command -v git &> /dev/null; then
    git submodule update --init --recursive || true
fi

# Bun
if command -v bun &> /dev/null; then
    bun install
else
    echo "[warn] Bun not found. Install from https://bun.sh"
fi

echo "[setup] Done. Run: make test"
