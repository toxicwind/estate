#!/usr/bin/env bash
# ============================================================================
# MAXFIX v1 - dynamic end-to-end yote recovery
# Phases: tailscale -> nim-proxy/flock -> durable units -> bridge backends
#         -> funnel map -> squawk(verify-only) -> pitchfork daemons -> verify
# Dynamic: every phase probes real state first, acts only on what's broken.
# Error cases: wedged listener / stale holder / dead proc / missing unit /
#              unit fails -> ad-hoc fallback / funnel drift (reported).
# NEVER: touches squawk processes, restarts user@1000.service, reboots.
# Safe to re-run. Log: /tmp/maxfix-<timestamp>.log
# ============================================================================
set -u
LOG="/tmp/maxfix-$(date +%Y%m%d-%H%M%S).log"
echo "logging to $LOG"
exec > >(tee -a "$LOG") 2>&1

say()  { echo "[maxfix] $*"; }
ok()   { echo "[maxfix] OK: $*"; }
warn() { echo "[maxfix] WARN: $*"; }

listening()  { ss -ltn 2>/dev/null | grep -q ":$1 "; }
holder_pid() { ss -ltnp 2>/dev/null | grep ":$1 " | grep -oP 'pid=\K[0-9]+' | head -1; }
pat_pids()   { pgrep -f "$1" 2>/dev/null | grep -v -e "^$$\$" -e "^$PPID\$" || true; }

say "--- phase 0: env ---"
if [ -f /home/toxic/.secrets ]; then set -a; . /home/toxic/.secrets; set +a; ok "sourced secrets"; else warn "no .secrets"; fi

say "--- phase 1: tailscaled ---"
if systemctl is-active --quiet tailscaled 2>/dev/null; then ok "tailscaled active";
else warn "tailscaled down, starting"; sudo systemctl start tailscaled 2>&1 | tail -1 || warn "start failed"; fi

say "--- phase 2: nim-proxy (flock) :25193 ---"
if ! listening 25193; then
  warn ":25193 down - reviving flock"
  h=$(holder_pid 25193); [ -n "$h" ] && { warn "stale holder pid $h"; kill -9 "$h" 2>/dev/null; sleep 2; }
  cd /home/toxic/sovereign 2>/dev/null || warn "no sovereign dir"
  ./bin/pitchfork-restart flock 2>&1 | tail -3
  sleep 6
fi
listening 25193 && ok ":25193 listening (nim-proxy alive)" || warn ":25193 STILL DOWN - agents have no model route"

say "--- phase 3: durable units ---"
mkdir -p /home/toxic/.config/systemd/user
VENV=/home/toxic/.awrawr-mcp-venv/bin/python
MCP_SCRIPT=/home/toxic/sovereign/projects/bridge/yote/awrawr_mcp.py
WS_SCRIPT=/home/toxic/sovereign/bridge/awrawr_ws_exec.py
make_unit() {
  local u=$1 desc=$2 script=$3 dir unitf
  dir=$(dirname "$script"); unitf=/home/toxic/.config/systemd/user/$u.service
  if [ -f "$unitf" ]; then ok "unit $u exists";
  else
    warn "unit $u missing - creating"
    cat > "$unitf" << EOF
[Unit]
Description=$desc
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$dir
ExecStart=/bin/bash -c 'set -a; [ -f /home/toxic/.secrets ] && . /home/toxic/.secrets; set +a; exec $VENV $script'
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF
    ok "unit $u written"
  fi
  systemctl --user daemon-reload 2>/dev/null || warn "daemon-reload failed"
  systemctl --user enable "$u.service" 2>/dev/null && ok "unit $u enabled" || warn "enable $u failed"
}
make_unit awrawr-mcp "awrawr MCP bridge backend (funnel /mcp -> 127.0.0.1:25198)" "$MCP_SCRIPT"
make_unit awrawr-ws-exec "awrawr WS exec bridge backend (funnel /exec-ws -> 127.0.0.1:25204)" "$WS_SCRIPT"

say "--- phase 4: bridge backends (dynamic repair) ---"
probe_mcp() {
  local code
  code=$(curl -s -m 8 -o /dev/null -w "%{http_code}" -X POST http://127.0.0.1:25198/mcp \
    -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' 2>/dev/null || echo "000")
  [ "$code" != "000" ]
}
probe_ws() {
  curl -s -m 8 -i http://127.0.0.1:25204/exec-ws -H "Connection: Upgrade" -H "Upgrade: websocket" \
    -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" 2>/dev/null | grep -q "101"
}
kill_stale() {
  local h pids
  h=$(holder_pid "$1")
  [ -n "$h" ] && { warn "$3: killing stale port holder pid $h"; kill -9 "$h" 2>/dev/null; }
  pids=$(pat_pids "$2")
  for p in $pids; do warn "$3: killing stale pid $p"; kill -9 "$p" 2>/dev/null; done
  sleep 2
}
adhoc_start() {
  local dir; dir=$(dirname "$1")
  say "$2: ad-hoc start"
  cd "$dir" || return 1
  setsid nohup "$VENV" "$1" >>"$3" 2>&1 < /dev/null &
  cd - >/dev/null || true
  sleep 5
}
ensure_backend() {
  local port=$1 unit=$2 name=$3 script=$4 pat=$5 probe=$6
  if listening "$port" && "$probe"; then ok "$name :$port healthy"; return 0; fi
  warn "$name :$port down or wedged - repairing"
  kill_stale "$port" "$pat" "$name"
  if [ -x "$VENV" ] && [ -f "$script" ]; then
    say "$name: trying unit $unit"
    systemctl --user start "$unit.service" 2>/dev/null || warn "$name: unit start failed"
    sleep 6
    if listening "$port" && "$probe"; then ok "$name :$port UP via unit"; return 0; fi
    warn "$name: unit did not bring it up - ad-hoc fallback"
    kill_stale "$port" "$pat" "$name"
    adhoc_start "$script" "$name" "/tmp/$name.log"
    if listening "$port" && "$probe"; then ok "$name :$port UP via ad-hoc (unit needs attention)"; return 0; fi
  else
    warn "$name: missing venv or script"
  fi
  warn "$name :$port FAILED - log tail:"; tail -5 "/tmp/$name.log" 2>/dev/null || true
  return 1
}
ensure_backend 25198 awrawr-mcp "awrawr-mcp" "$MCP_SCRIPT" 'awrawr_mcp\.py' probe_mcp
ensure_backend 25204 awrawr-ws-exec "awrawr-ws" "$WS_SCRIPT" 'awrawr_ws_exec\.py' probe_ws

say "--- phase 5: funnel map ---"
SERVE_OUT=""
if tailscale serve status 2>/dev/null | grep -q '/mcp'; then SERVE_OUT=$(tailscale serve status 2>/dev/null);
elif sudo -n true 2>/dev/null && sudo tailscale serve status 2>/dev/null | grep -q '/mcp'; then SERVE_OUT=$(sudo tailscale serve status 2>/dev/null);
else warn "cannot read serve status"; fi
if [ -n "$SERVE_OUT" ]; then
  echo "$SERVE_OUT" | grep -E '/mcp |/exec-ws ' | head -4
  echo "$SERVE_OUT" | grep -F '/mcp ' | grep -q '25198' && ok "/mcp -> :25198" || warn "/mcp mapping wrong/missing"
  echo "$SERVE_OUT" | grep -F '/exec-ws ' | grep -q '25204' && ok "/exec-ws -> :25204" || warn "/exec-ws mapping wrong/missing"
fi

say "--- phase 6: squawk verify-only ---"
listening 25147 && ok "squawk-ws :25147 alive" || warn "squawk-ws DOWN (verify-only, not touching)"
listening 25135 && ok "squawk-feed :25135 alive" || warn "squawk-feed DOWN (verify-only, not touching)"

say "--- phase 7: pitchfork stopped daemons ---"
cd /home/toxic/sovereign 2>/dev/null || warn "no sovereign dir"
if pitchfork list >/dev/null 2>&1; then
  STOPPED=$(pitchfork list 2>/dev/null | grep -i 'stopped' | awk '{print $1}' || true)
  if [ -z "$STOPPED" ]; then ok "no stopped daemons";
  else for d in $STOPPED; do
    n=${d##*/}
    [ "$n" = "tau" ] && { say "tau intentionally manual - skipping"; continue; }
    if [ "$n" = "flock" ] && listening 25193; then ok "flock already up"; continue; fi
    say "restarting stopped daemon: $n"
    ./bin/pitchfork-restart "$n" 2>&1 | tail -2
  done; fi
else warn "pitchfork list failed"; fi

say "--- phase 8: end-to-end verification ---"
C1=$(curl -s -m 8 -o /dev/null -w "%{http_code}" -X POST http://127.0.0.1:25198/mcp -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' 2>/dev/null || echo "000")
say "local  /mcp       http=$C1"
C2=$(curl -s -m 8 -i http://127.0.0.1:25204/exec-ws -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" 2>/dev/null | head -1 | tr -d '\r')
say "local  /exec-ws     -> $C2"
C3=$(curl -s -m 12 -o /dev/null -w "%{http_code}" https://github-mcp-host.tailc9ac71.ts.net/mcp 2>/dev/null || echo "000")
say "funnel /mcp       http=$C3"
C4=$(curl -s -m 12 -i https://github-mcp-host.tailc9ac71.ts.net/exec-ws -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" 2>/dev/null | head -1 | tr -d '\r')
say "funnel /exec-ws     -> $C4"
C5=$(curl -s -m 8 -o /dev/null -w "%{http_code}" http://127.0.0.1:25100/v1/models 2>/dev/null || echo "000")
say "herd   /v1/models http=$C5"
if [ "$C5" = "200" ]; then
  python3 - << 'PYEOF' 2>&1 | tail -4
import json, urllib.request
try:
    models = json.load(urllib.request.urlopen("http://127.0.0.1:25100/v1/models", timeout=8))
    ids = [m["id"] for m in models.get("data", [])]
    print("models:", len(ids))
    if ids:
        m = ids[0]
        req = urllib.request.Request("http://127.0.0.1:25100/v1/chat/completions",
            data=json.dumps({"model": m, "messages": [{"role": "user", "content": "reply with exactly: ROUTER_OK"}], "max_tokens": 16}).encode(),
            headers={"Content-Type": "application/json"})
        r = json.load(urllib.request.urlopen(req, timeout=60))
        txt = r["choices"][0]["message"]["content"].strip()
        print("completion via", m, "->", txt[:40])
except Exception as e:
    print("completion probe:", type(e).__name__, str(e)[:120])
PYEOF
fi
say "=== MAXFIX done ==="
ss -ltn | grep -E ':(25193|25198|25204|25100|25147|25135) ' || true
say "log: $LOG"
