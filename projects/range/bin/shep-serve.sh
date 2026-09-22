#!/bin/sh
# shep-serve.sh -- launch shep (mcptools MCP gateway) with secrets from /home/toxic/.secrets.
#
# Secret hygiene: shep persists the EFFECTIVE config back to mcp_config.json on
# every start, re-materializing live secrets (api_key, server env) into the file.
# Therefore:
#   - mcp_config.json is NEVER tracked in git (see .gitignore).
#   - mcp_config.json.dist IS tracked: a scrubbed template with REDACTED
#     placeholders, used to bootstrap the live config on fresh checkouts.
#   - Secrets always come from /home/toxic/.secrets at runtime, never from disk.
set -e
SECRETS=/home/toxic/.secrets
CFG=/home/toxic/sovereign/projects/range/ranch/barn/shep/mcp_config.json
DIST=/home/toxic/sovereign/projects/range/ranch/barn/shep/mcp_config.json.dist

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
  # Fresh checkout: bootstrap the live config from the scrubbed template.
  cp "$DIST" "$CFG"
  chmod 600 "$CFG"
fi

exec /home/toxic/sovereign/projects/range/bin/shep serve \
  --config="$CFG" \
  --log-level=warn --log-to-file \
  --listen=127.0.0.1:25127 "$@"
