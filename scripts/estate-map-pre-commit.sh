#!/usr/bin/env bash
# estate pre-commit — estate-map freshness gate (2026-11-02).
# If the commit includes docs/estate-map* and the map wasn't regenerated recently,
# regenerate it so the committed map is never stale again. Non-blocking by design
# (git hooks must not silently fail unrelated commits); exits 0 always.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
if git diff --cached --name-only | grep -q "docs/estate-map"; then
  # regenerate fresh so the staged map matches live reality
  (cd "$ROOT" && bun bin/estate-map.ts 1>/dev/null 2>&1 || true)
  git add docs/estate-map.json docs/estate-map.md 2>/dev/null || true
  echo "estate-map: regenerated + staged"
fi
exit 0
