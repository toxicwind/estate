#!/usr/bin/env bash
# squawk-health.sh — first-class hosting health probe for Squawk (toxicwind/squawk)
# file-based chat: no daemon to supervise; this verifies the deployment is healthy.
# exit 0 = healthy, 1 = degraded (prints FAIL lines). Pass --write-test for a post/read round-trip.
set -u
ROOT=/home/toxic/.shingle/chat
KEYS=/home/toxic/.shingle/keys
fail=0
say() { [ "$1" = OK ] && echo "OK: $2" || { echo "FAIL: $2"; fail=1; }; }
[ -d "$ROOT/.git" ] && say OK "chat root $ROOT is a git repo" || say FAIL "chat root missing/not a repo"
remote=$(git -C "$ROOT" remote get-url origin 2>/dev/null)
case "$remote" in *toxicwind/squawk*) say OK "origin=$remote";; *) say FAIL "origin unexpected: $remote";; esac
for id in breaker shingle agent1 yote relay; do
  k="$KEYS/$id.key"
  if [ -f "$k" ]; then
    perms=$(stat -c %a "$k")
    [ "$perms" = 600 ] && say OK "key $id present (0600)" || say FAIL "key $id perms=$perms (want 600)"
  else say FAIL "key $id missing"; fi
done
for ch in fleet leads; do
  [ -f "$ROOT/$ch/_meta.json" ] && say OK "channel $ch initialized" || say FAIL "channel $ch missing"
done
export AGENT_CHAT_ROOT="$ROOT"
if python3 "$ROOT/chat.py" read fleet --as agent1 >/dev/null 2>&1; then say OK "fleet read (HMAC verify path) works"; else say FAIL "fleet read failed"; fi
if [ "${1:-}" = "--write-test" ]; then
  if python3 "$ROOT/chat.py" post fleet --from shingle --title health --body "health probe $(date -u +%FT%TZ)" >/dev/null 2>&1; then say OK "post/read round-trip works"; else say FAIL "post failed"; fi
fi
exit $fail
