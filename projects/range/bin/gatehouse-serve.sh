#!/bin/sh
# gatehouse-serve.sh -- mcpproxy-go gateway
set -e
SECRETS=/home/toxic/.secrets
CFG=/home/toxic/sovereign/projects/range/ranch/barn/gatehouse/mcp_config.json
DIST=/home/toxic/sovereign/projects/range/ranch/barn/gatehouse/mcp_config.json.dist
if [ -f "$SECRETS" ]; then
  # shellcheck disable=SC1090
  . "$SECRETS"
fi
: "${MCPPROXY_API_KEY:?MCPPROXY_API_KEY missing from $SECRETS}"
export MCPPROXY_API_KEY
if [ -n "${EXA_API_KEY:-}" ]; then
  export EXA_API_KEY
fi
if [ ! -f "$CFG" ]; then
  cp "$DIST" "$CFG"
  chmod 600 "$CFG"
fi
exec /home/toxic/sovereign/projects/range/bin/gatehouse serve \
  --config="$CFG" \
  --log-level=warn --log-to-file \
  --listen=127.0.0.1:25127 "$@"
