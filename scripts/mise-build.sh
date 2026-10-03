#!/usr/bin/env bash
# Estate build check through the configured mise toolchain.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
mise exec -- bun test tests/ports.test.ts
mise exec -- bun test tests/open_web_uis.test.ts
for script in scripts/*.sh; do
  bash -n "$script"
done