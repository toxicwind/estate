#!/usr/bin/env bash
# scripts/flicker-build.sh — sovereign-projects build entry point.
#
# Submits the repo's canonical build+test command to the flicker build-job
# daemon (http://127.0.0.1:25148, override with FLICKER_URL), polls the job,
# and exits 0 only when the job succeeds — or when an identical command
# already succeeded (CACHED).
#
#   ./scripts/flicker-build.sh
#   FLICKER_REPO=/path/to/checkout ./scripts/flicker-build.sh  # override repo
set -euo pipefail

FLICKER="${FLICKER_URL:-http://127.0.0.1:25148}"
NAME="sovereign-build"
if [ -n "${FLICKER_REPO:-}" ]; then
  REPO="$FLICKER_REPO"
else
  REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

# Canonical bounded check, taken from the repo's own CI
# (.github/workflows/sovereign-ci.yml): the bun test suites plus a syntax
# check of scripts/*.sh. Needs no node_modules (bun:test + node builtins
# only). The CI's router build step is intentionally excluded — it requires
# the ranch checkout under projects/range/ranch, which is not present.
CMD="export PATH=\"\$HOME/.local/share/mise/shims:\$HOME/.bun/bin:/usr/local/bin:\$PATH\"; cd \"$REPO\" && bun test tests/ports.test.ts && bun test tests/open_web_uis.test.ts && for f in scripts/*.sh; do if [ -f \"\$f\" ]; then bash -n \"\$f\" || exit 1; fi; done"

payload="$(python3 -c 'import json,sys; print(json.dumps({"name": sys.argv[1], "command": sys.argv[2]}))' "$NAME" "$CMD")"
resp="$(curl -sS -m 30 -X POST "$FLICKER/api/jobs" -H 'Content-Type: application/json' -d "$payload")"
id="$(printf '%s' "$resp" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')" \
  || { echo "submit failed: $resp" >&2; exit 1; }
[ -n "$id" ] || { echo "submit failed: $resp" >&2; exit 1; }

if printf '%s' "$resp" | python3 -c 'import json,sys; raise SystemExit(0 if json.load(sys.stdin).get("cached") else 1)'; then
  echo "CACHED (id $id) — identical job already succeeded"
  exit 0
fi

echo "submitted job $id — polling $FLICKER/api/jobs/$id"
# 1800s: covers deep queue waits on a shared daemon plus the run itself.
# Poll every 2s per the flicker interface.
deadline=$((SECONDS + 1800))
while :; do
  st="$(curl -sS -m 15 "$FLICKER/api/jobs/$id" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("status",""))')"
  case "$st" in
    success) echo "SUCCESS (id $id)"; exit 0 ;;
    failure)
      echo "FAILURE (id $id) — logs:" >&2
      curl -sS -m 30 "$FLICKER/api/jobs/$id/logs" || true
      exit 1 ;;
  esac
  if [ "$SECONDS" -ge "$deadline" ]; then echo "TIMEOUT (id $id)" >&2; exit 1; fi
  sleep 2
done
