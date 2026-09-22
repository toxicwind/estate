#!/usr/bin/env bash
# Acceptance probe: openfang agents live on the mesh.
# Exits 0 only if the full chain works: shep -> shim -> openfang mcp -> coyote.
set -u
SHEP=/home/toxic/sovereign/mesh/bin/shep
CFG=/home/toxic/sovereign/mesh/gateway/mcp_config.json
fail() { echo "PROBE-FAIL: $1" >&2; exit 1; }

line=$($SHEP -c "$CFG" upstream list 2>/dev/null | grep -i openfang) || fail "openfang missing from upstream list"
echo "$line" | grep -q "Connected" || fail "openfang not Connected: $line"
ntools=$(echo "$line" | grep -oE '[0-9]+ tools' | grep -oE '[0-9]+' | head -1)
[ "${ntools:-0}" -ge 1 ] || fail "no tools discovered"

out=$($SHEP -c "$CFG" call tool-write --tool-name=openfang:openfang_agent_coyote \
  --json_args='{"message":"Reply with exactly: MESH-PROBE-OK"}' \
  --timeout 90s --reason "openfang mesh acceptance probe" -o json 2>&1) || fail "tool call errored"
echo "$out" | grep -q "MESH-PROBE-OK" || fail "coyote did not return MESH-PROBE-OK"

echo "PROBE-PASS: openfang connected, $ntools tools, live coyote call returned MESH-PROBE-OK"
