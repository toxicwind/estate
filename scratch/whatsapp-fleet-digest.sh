#!/usr/bin/env bash
# WhatsApp fleet digest reader: pulls the zipfs-vault (unsealed squawk traffic),
# diffs the manifest against the cursor, prints new messages IRC-style.
# Does NOT advance the cursor itself: it prints a trailing CURSOR=<n> line and
# the caller advances the cursor only after successfully delivering the digest
# (redelivery on failure beats silent loss).
# Output: digest lines, then CURSOR=<n>. Prints NO_NEW_TRAFFIC when quiet.
set -euo pipefail

CURSOR="$HOME/workspace/whatsapp-fleet-digest.cursor"
VAULT="$HOME/workspace/skills/zipfs-vault/runner.sh"

old="0"
[ -f "$CURSOR" ] && old="$(cat "$CURSOR")"

if ! "$VAULT" pull >/dev/null 2>&1; then
  echo "DIGEST_ERROR: vault pull failed" >&2
  exit 1
fi

new_json="$("$VAULT" list --json 2>/dev/null | jq -c --argjson old "$old" '
  [ to_entries[]
    | select(.key | test("^fleet/[0-9]+$"))
    | {alias: .key, seq: (.key | sub("^fleet/";"") | tonumber)}
    | select(.seq > $old) ]
  | sort_by(.seq) | .[:20]')"
[ -z "$new_json" ] && new_json="[]"

count="$(printf '%s' "$new_json" | jq 'length')"
if [ "$count" = "0" ]; then
  echo "NO_NEW_TRAFFIC"
  exit 0
fi

printf '%s' "$new_json" | jq -r '.[].alias' | while IFS= read -r alias; do
  [ -z "$alias" ] && continue
  seq="${alias#fleet/}"
  env="$("$VAULT" get "$alias" 2>/dev/null || echo '{}')"
  sender="$(printf '%s' "$env" | jq -r '.sender // "?"' 2>/dev/null)"
  sealed="$(printf '%s' "$env" | jq -r '.sealed // false' 2>/dev/null)"
  if [ "$sealed" = "true" ]; then
    printf '[#fleet] <%s> [sealed message]\n' "$sender"
  else
    text="$(printf '%s' "$env" | jq -r '(.text // "" | tostring)[:400]' 2>/dev/null)"
    printf '[#fleet] <%s> %s\n' "$sender" "$text"
  fi
done

new="$(printf '%s' "$new_json" | jq -r '.[-1].seq')"
printf 'CURSOR=%s\n' "$new"
