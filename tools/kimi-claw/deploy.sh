#!/usr/bin/env bash
# KimiClaw repair deploy — idempotent. Safe to re-run.
# Deploys: bridge.ts, instances/kimiclaw-{a,b}.json, pitchfork daemons
#          sovereign/kimiclaw-a and sovereign/kimiclaw-b (squawk fleet relays).
# Does NOT touch the bridge (awrawr-ws-exec) or any squawk process.
set -euo pipefail

KC_DIR="/home/toxic/sovereign/tools/kimi-claw"
PF="/home/toxic/.local/share/mise/installs/pitchfork/2.25.0/pitchfork"
BUN="/home/toxic/.bun/bin/bun"
TOML="/home/toxic/sovereign/pitchfork.toml"

say() { echo "[deploy] $*"; }

# --- 1. sanity: files present -------------------------------------------
for f in "$KC_DIR/bridge.ts" "$KC_DIR/instances/kimiclaw-a.json" "$KC_DIR/instances/kimiclaw-b.json"; do
  [ -f "$f" ] || { say "MISSING $f — aborting"; exit 2; }
done
command -v "$BUN" >/dev/null || { say "bun not found — aborting"; exit 2; }
say "files present"

# --- 2. syntax check -----------------------------------------------------
"$BUN" build "$KC_DIR/bridge.ts" --target bun --outfile /dev/null >/dev/null 2>&1 \
  && say "bun build OK" || { say "bun build FAILED"; exit 2; }

# --- 3. route validation, both instances (fail-fast) ---------------------
"$BUN" "$KC_DIR/bridge.ts" --instance a --check-route || { say "instance a routes FAIL"; exit 2; }
"$BUN" "$KC_DIR/bridge.ts" --instance b --check-route || { say "instance b routes FAIL"; exit 2; }
say "both instances route-checked"

# --- 4. register pitchfork daemons (append once) -------------------------
cp "$TOML" "$TOML.bak-$(date +%Y%m%d-%H%M%S)"
for inst in a b; do
  if grep -q "^\[daemons\.kimiclaw-$inst\]" "$TOML"; then
    say "pitchfork daemon kimiclaw-$inst already registered"
  else
    cat >> "$TOML" <<EOF

[daemons.kimiclaw-$inst]
run = "exec $BUN $KC_DIR/bridge.ts --daemon --instance $inst"
dir = "$KC_DIR"
mise = false
retry = true
ready_cmd = "pgrep -f 'bridge.ts --daemon --instance $inst' >/dev/null"
auto = ["start"]
EOF
    say "registered pitchfork daemon kimiclaw-$inst"
  fi
done

# --- 5. start (or confirm running) ---------------------------------------
for inst in a b; do
  if "$PF" status "sovereign/kimiclaw-$inst" 2>/dev/null | grep -q running; then
    say "kimiclaw-$inst already running"
  else
    "$PF" start "sovereign/kimiclaw-$inst"
    say "started kimiclaw-$inst"
  fi
done
say "deploy complete"
