#!/usr/bin/env bash
# yote-resync-token.sh — one-block bridge token re-sync for yote.
# Mints a fresh token, installs it, restarts the pitchfork daemon, verifies.
# Prints the new token for entry into the custom.awrawr-mcp vault page.
# Run on yote as toxic. Never prints the old token. Never touches squawk.
set -euo pipefail

NEWTOK=$(python3 -c "import secrets;print(secrets.token_urlsafe(48))")
printf '%s' "$NEWTOK" > ~/.awrawr_mcp_token
chmod 600 ~/.awrawr_mcp_token
echo "new fingerprint: $(sha256sum ~/.awrawr_mcp_token | cut -c1-16)"

PF=$(ls -d /home/toxic/.local/share/mise/installs/pitchfork/*/pitchfork 2>/dev/null | sort -V | tail -1)
[ -z "$PF" ] && { echo "ABORT: pitchfork not found"; exit 1; }
"$PF" restart sovereign/awrawr-ws-exec 2>&1 | tail -1
sleep 3
if ss -tlnp 2>/dev/null | grep -q ':8379 '; then
  echo "daemon listening on 127.0.0.1:8379"
else
  echo "ABORT: daemon not listening on 8379 after restart"; exit 1
fi

echo "=== enter this value in the awrawr-mcp vault page (NOT in chat) ==="
cat ~/.awrawr_mcp_token; echo
echo "After submitting, hatch's daemon re-fetches the credential on reconnect;"
echo "expect HTTP 101 on the next handshake (rm ~/.cache/awrawr-ws-down on hatch if a stale 15s flag 502s the first try)."
