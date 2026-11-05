#!/usr/bin/env bash
# install-hooks.sh — auto-wire the estate git hooks (core.hooksPath=.githooks).
# Run once after clone (or via package.json postinstall). Makes the eternal
# coverage-gate + estate-map pre-commit hooks auto-active on every checkout.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
git config core.hooksPath .githooks
echo "estate hooks: core.hooksPath -> .githooks (eternal coverage gate + estate-map active)"