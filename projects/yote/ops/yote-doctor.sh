#!/usr/bin/env bash
# yote-doctor.sh v2 — diagnose the yote bridge AND every tailscale-serve backend.
# Diagnose-only: changes nothing. Run: sudo ./yote-doctor.sh
# v2 changes vs v1:
#   - reads the backend map from `tailscale serve status --json` (tailscaled
#     owns 443 via Funnel; there is no Caddy/nginx on this box)
#   - checks every serve backend port individually (mcp, exec-ws, gemini-mcp,
#     squawk-ws, squawk-feed, whatsapp-webhook, /, /files) incl. squawk
#   - probes via the real tailnet DNS name (correct SNI); never 127.0.0.1:443
#     with SNI=localhost (that causes the TLSV1_ALERT_INTERNAL_ERROR)
#   - a failed probe is a FAIL. curl exit != 0 is never "route alive".
#   - shows full process cmdlines (no 90-char truncation)
set -u
LOG=/tmp/yote-doctor-v2.log
: > "$LOG" 2>/dev/null || LOG=/dev/null

say()  { echo "$@" | tee -a "$LOG"; }
row()  { printf '%-6s %-16s %s\n' "$1" "$2" "$3" | tee -a "$LOG"; }
hdr()  { say "== $1 =="; }

SUDO=""
[ "$(id -u)" -ne 0 ] && SUDO="sudo"

hdr "yote-doctor v2"
say "kernel=$(uname -r) cpus=$(nproc) mem=$(free -g | awk '/^Mem:/{print $2}')G"
say "date=$(date -u +%FT%TZ)"

# ---- token ----
hdr "token"
TOK="$HOME/.awrawr_mcp_token"
[ "$(id -u)" -eq 0 ] && TOK="/home/toxic/.awrawr_mcp_token"
if [ -f "$TOK" ]; then
  fp=$(sha256sum "$TOK" | cut -c1-16)
  row ok token "$TOK present, fp $fp"
else
  row fail token "$TOK MISSING"
fi

# ---- tailscale ----
hdr "tailscale"
if tailscale status >/dev/null 2>&1; then
  ip4=$(tailscale ip -4 2>/dev/null | head -1)
  row ok tailscale "online ($ip4)"
else
  row fail tailscale "tailscale status failed"
fi

# ---- serve map ----
hdr "tailscale serve map"
SERV_JSON=$($SUDO tailscale serve status --json 2>/dev/null)
if [ -z "$SERV_JSON" ]; then
  row fail serve "could not read serve status"
  SERV_JSON="{}"
fi
ROUTES_TSV=$(printf '%s' "$SERV_JSON" | python3 -c '
import json,sys
try:
    data=json.load(sys.stdin)
except Exception as e:
    print("ERR\t\t"+str(e)); sys.exit(0)
web=data.get("Web") or {}
for frontend,cfg in web.items():
    host=frontend.rsplit(":",1)[0]
    for path,h in ((cfg.get("Handlers") or {}).items()):
        print("\t".join([host,path,(h.get("Proxy") or "")]))
' 2>/dev/null)
if [ -z "$ROUTES_TSV" ]; then
  row warn serve "no proxy routes found in serve status"
else
  while IFS=$'\t' read -r host path proxy; do
    [ "$host" = "ERR" ] && { row fail serve "parse error: $path"; continue; }
    say "  route https://$host$path -> $proxy"
  done <<< "$ROUTES_TSV"
fi

# ---- per-backend port checks ----
hdr "backend ports (from serve map)"
ALL_OK=1
while IFS=$'\t' read -r host path proxy; do
  [ -z "$proxy" ] && continue
  [ "$host" = "ERR" ] && continue
  # proxy looks like http://127.0.0.1:8377/mcp
  port=$(printf '%s' "$proxy" | sed -n 's#.*://[^:/]*:\([0-9]*\).*#\1#p')
  [ -z "$port" ] && continue
  if $SUDO ss -tln 2>/dev/null | grep -q ":$port\b"; then
    listener=$($SUDO ss -tlnp 2>/dev/null | grep ":$port\b" | head -1 | sed 's/.*users:(//;s/)).*//')
    row ok "port:$port" "$path backend listening ($listener)"
  else
    row fail "port:$port" "$path backend NOT listening ($proxy)"
    ALL_OK=0
  fi
done <<< "$ROUTES_TSV"

# ---- per-route HTTPS probes (correct SNI via tailnet name) ----
hdr "route probes (tailnet DNS, correct SNI)"
while IFS=$'\t' read -r host path proxy; do
  [ -z "$host" ] && continue
  [ "$host" = "ERR" ] && continue
  code=$(curl -sk --max-time 8 -o /dev/null -w '%{http_code}' "https://$host$path" 2>/dev/null)
  rc=$?
  if [ $rc -eq 0 ]; then
    # any HTTP answer (even 400/404/426 on ws paths) proves TLS+route alive
    row ok "probe:$path" "HTTPS $code via $host"
  else
    row fail "probe:$path" "curl failed rc=$rc (backend or route down)"
    ALL_OK=0
  fi
done <<< "$ROUTES_TSV"

# ---- processes ----
hdr "processes (full cmdlines)"
procs=$(pgrep -af "awrawr|ws_exec|squawk|_mcp|mcp-" 2>/dev/null | grep -v "yote-doctor" | grep -v "pgrep -af")
if [ -z "$procs" ]; then
  row warn procs "no awrawr/squawk/mcp processes running"
else
  while IFS= read -r line; do
    pid=$(printf '%s' "$line" | awk '{print $1}')
    full=$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null)
    say "  pid $pid: $full"
  done <<< "$procs"
  row ok procs "$(printf '%s' "$procs" | wc -l) matching process(es)"
fi

# ---- listening sockets with owners ----
hdr "listening sockets"
$SUDO ss -tlnp 2>/dev/null | awk 'NR>1 {print "  "$4"  "$NF}' | sort -u | head -25

# ---- squawk (important: report only, never touch) ----
hdr "squawk"
for p in 25147 25135; do
  if $SUDO ss -tln 2>/dev/null | grep -q ":$p\b"; then
    row ok "squawk:$p" "listening"
  else
    row fail "squawk:$p" "NOT listening"
    ALL_OK=0
  fi
done
WS=/home/toxic/sovereign/shingle-workspace
for pf in "$WS/squawk-ws-client.pid" "$WS/service-health-poller.pid"; do
  if [ -f "$pf" ]; then
    pid=$(cat "$pf" 2>/dev/null)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      row ok "pidfile" "$pf -> $pid alive"
    else
      row warn "pidfile" "$pf -> $pid STALE"
    fi
  fi
done
pgrep -af "squawk" | grep -v "yote-doctor" | grep -v "pgrep" | head -5 | sed 's/^/  /'

# ---- server discovery (what SHOULD be running) ----
hdr "server discovery"
for f in "$WS/awrawr_ws_exec.py" "$WS/squawk_ws_server.py" "$WS/squawk-ws-client.py"; do
  [ -f "$f" ] || continue
  say "  $f:"
  grep -nE 'PORT|port ?[=:] ?[0-9]{4,5}|:[0-9]{4,5}' "$f" 2>/dev/null | head -8 | sed 's/^/    /'
done
say "  bin dirs:"
for d in "$WS/bin" /home/toxic/sovereign/gear-lane1-20260914/awrawr-mcp/bin /home/toxic/worktrees/ctm-mode-fix/gear/awrawr-mcp/bin; do
  [ -d "$d" ] && say "    $d: $(ls "$d" 2>/dev/null | tr '\n' ' ')"
done
say "  systemd units mentioning mcp/awrawr/squawk:"
systemctl list-units --all 2>/dev/null | grep -iE 'mcp|awrawr|squawk' | head -5 | sed 's/^/    /'
$SUDO -u toxic systemctl --user list-units --all 2>/dev/null | grep -iE 'mcp|awrawr|squawk' | head -5 | sed 's/^/    /'

hdr "summary"
if [ "$ALL_OK" = "1" ]; then
  row ok overall "all serve backends listening and reachable"
else
  row fail overall "one or more serve backends DOWN (see above)"
fi
say "full log: $LOG"
