#!/usr/bin/env bash
# yote-fix.sh v3 — auto-apply repair for the awrawr-mcp bridge on Yote (awrawr-pc).
#
# v3 changes (2026-09-20):
#   - v2's discovery grepped for the port digits and started the first .py
#     hit — on the real box that was a numpy TEST FILE. v3 is confidence-gated:
#     never start anything under */venv/*, */site-packages/*, */node_modules/*,
#     */.cache/*, */tests/*, *test_*.py, *_test.py, or */archive*; a candidate
#     must contain a server marker (start_server, serve_forever, uvicorn,
#     Flask(, FastAPI(, http.server, websockets, asyncio) AND a mention of the
#     port. Up to 3 candidates per port, in preference order (running-process
#     cwds, then shingle-workspace, then bin dirs); no confident candidate ->
#     REPORT-AND-SKIP, never start a guess; never start an already-running
#     file; never attempt the same file twice in one run.
#
# v2 changes (2026-09-20):
#   - REMOVED the v1 "bridge:start" autostart. It launched exec.py, which is the
#     HATCH-side command client (exits in milliseconds) — that was the
#     "autostart died" bug. Nothing hatch-side is ever started on yote.
#   - The REAL yote servers are discovered, never hardcoded. The backend map
#     comes from `tailscale serve status --json`; a dead backend's server file
#     is found by searching .py sources for the backend's port number.
#   - Deploy is gist-only. raw.githubusercontent.com/toxicwind/gear is dead
#     (no such repo); the gist mirror is the only source.
#   - All TLS probes use the tailnet DNS name for SNI. Probing the raw tail IP
#     (or 127.0.0.1 with SNI=localhost) through Tailscale Serve/Funnel causes
#     TLSV1_ALERT_INTERNAL_ERROR — that was a probe defect, not a server defect.
#   - Covers ALL serve backends, not just /exec-ws and /mcp.
#   - NEVER kills a live squawk process. Hands off, always.
#
# Usage: sudo ./yote-fix.sh [--dry-run] [--bridge-dir DIR] [--supervise]
#   --ref is accepted for backward compatibility but ignored (gist-only now).
#
# Exit codes: 0 all fixed & verified | 1 issues remain | 3 usage/environment error

set -u
DRYRUN=0
BRIDGE_DIR=""
SUPERVISE=0
prev=""
for a in "$@"; do
  if [ -n "$prev" ]; then
    case "$prev" in
      --ref) : ;;            # accepted, ignored: deploy is gist-only in v2
      --bridge-dir) BRIDGE_DIR="$a" ;;
    esac
    prev=""
    continue
  fi
  case "$a" in
    --dry-run) DRYRUN=1 ;;
    --supervise) SUPERVISE=1 ;;
    --ref=*|--ref) [ "$a" = "--ref" ] && prev="--ref" || : ;;
    --bridge-dir=*) BRIDGE_DIR="${a#--bridge-dir=}" ;;
    --bridge-dir) prev="$a" ;;
    -h|--help) sed -n '2,24p' "$0"; exit 0 ;;
    *) echo "unknown arg: $a" >&2; exit 3 ;;
  esac
done
[ -n "$prev" ] && { echo "$prev needs a value" >&2; exit 3; }

have() { command -v "$1" >/dev/null 2>&1; }
CHECKS=""
note() { CHECKS="${CHECKS}${1}|${2}|${3}"$'\n'; }
say()  { printf '%s\n' "$*"; }
TS="$(date +%Y%m%d-%H%M%S)"

if [ "$(id -u)" -ne 0 ]; then
  say "must run as root (sudo) — needs token file, process control, serve map"
  exit 3
fi
if ! have python3; then say "python3 required"; exit 3; fi

run() {  # run CMD...  (honors --dry-run)
  if [ "$DRYRUN" -eq 1 ]; then say "[dry-run] would run: $*"; return 0; fi
  "$@"
}

# --- 1. token hygiene (auto-applied; fingerprint only, never the value) -----------
TOKEN=""
for cand in ${SUDO_USER:+"/home/$SUDO_USER/.awrawr_mcp_token"} "$HOME/.awrawr_mcp_token" /home/toxic/.awrawr_mcp_token; do
  if [ -f "$cand" ]; then TOKEN="$cand"; break; fi
done
if [ -z "$TOKEN" ]; then
  note fail "token" "no .awrawr_mcp_token found — cannot fix auth without it"
elif [ ! -s "$TOKEN" ]; then
  note fail "token" "$TOKEN exists but is empty"
else
  FP_BEFORE="$(sha256sum "$TOKEN" | cut -c1-16)"
  if grep -q $'\r' "$TOKEN" 2>/dev/null; then
    if run sed -i 's/\r$//' "$TOKEN"; then
      note fixed "token" "stripped CR bytes ($TOKEN fp $FP_BEFORE -> $(sha256sum "$TOKEN" | cut -c1-16))"
    else note fail "token" "could not strip CR bytes"; fi
  elif grep -qE '^[[:space:]]+|[[:space:]]+$' "$TOKEN" 2>/dev/null; then
    if run sed -i 's/^[[:space:]]*//;s/[[:space:]]*$//' "$TOKEN"; then
      note fixed "token" "trimmed whitespace ($TOKEN fp $FP_BEFORE -> $(sha256sum "$TOKEN" | cut -c1-16))"
    else note fail "token" "could not trim whitespace"; fi
  else
    note ok "token" "$TOKEN clean, fp $FP_BEFORE"
  fi
fi

# --- 2. tailscale up (auto) --------------------------------------------------------
if have tailscale; then
  if tailscale status >/dev/null 2>&1; then
    note ok "tailscale" "online ($(tailscale ip -4 2>/dev/null | head -1))"
  elif have systemctl; then
    if run systemctl restart tailscaled 2>/dev/null; then
      sleep 2
      tailscale status >/dev/null 2>&1 \
        && note fixed "tailscale" "restarted tailscaled, now online" \
        || note fail "tailscale" "tailscaled restarted but still offline"
    else note fail "tailscale" "could not restart tailscaled"; fi
  else note fail "tailscale" "offline, no systemctl to restart it"; fi
else note fail "tailscale" "tailscale CLI not found — serve map unavailable"; fi

# --- 3. serve map: the source of truth for every backend ---------------------------
# tailscaled owns 443 via Funnel; there is no Caddy/nginx on this box.
SERV_JSON="$(tailscale serve status --json 2>/dev/null)"
ROUTES_TSV=""
TAILNAME=""
if [ -n "$SERV_JSON" ]; then
  ROUTES_TSV="$(printf '%s' "$SERV_JSON" | python3 -c '
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
' 2>/dev/null)"
  TAILNAME="$(printf '%s' "$ROUTES_TSV" | awk -F'\t' 'NR==1{print $1}')"
fi
# fall back to the known tailnet name if the map gave nothing usable
[ -z "$TAILNAME" ] || [ "$TAILNAME" = "ERR" ] && TAILNAME="github-mcp-host.tailc9ac71.ts.net"
note ok "serve:map" "tailnet name $TAILNAME ($(printf '%s' "$ROUTES_TSV" | grep -c $'\t' || true) routes)"
while IFS=$'\t' read -r host path proxy; do
  [ -z "$host" ] || [ "$host" = "ERR" ] && continue
  say "  route https://$host$path -> $proxy"
done <<< "$ROUTES_TSV"

port_of() {  # proxy URL -> port number
  printf '%s' "$1" | sed -n 's#.*://[^:/]*:\([0-9]*\).*#\1#p'
}
port_listening() {  # $1=port -> 0 if something listens
  ss -tln 2>/dev/null | grep -q ":$1\b"
}
listener_of() {  # $1=port -> "pid N (cmdline)" or ""
  _line="$(ss -tlnp 2>/dev/null | grep ":$1\b" | head -1)"
  [ -z "$_line" ] && return 1
  _pid="$(printf '%s' "$_line" | grep -oE 'pid=[0-9]+' | head -1 | cut -d= -f2)"
  _cmd="$(tr '\0' ' ' < "/proc/$_pid/cmdline" 2>/dev/null | cut -c1-120)"
  printf 'pid %s (%s)' "${_pid:-?}" "${_cmd:-unidentified}"
}

# --- 4. discover candidate server roots (never hardcoded) ---------------------------
# The intended tree is found, not assumed: prefer the cwd of a running
# awrawr/ws_exec/squawk process, then the known workspace if present.
SRV_ROOTS=""
for p in $(pgrep -f '[a]wrawr|[w]s_exec|[s]quawk' 2>/dev/null); do
  _cwd="$(readlink "/proc/$p/cwd" 2>/dev/null)"
  [ -n "$_cwd" ] && [ -d "$_cwd" ] && SRV_ROOTS="$SRV_ROOTS $_cwd"
done
[ -d /home/toxic/sovereign/shingle-workspace ] && SRV_ROOTS="$SRV_ROOTS /home/toxic/sovereign/shingle-workspace"
# de-dupe
SRV_ROOTS="$(printf '%s' "$SRV_ROOTS" | tr ' ' '\n' | awk 'NF && !seen[$0]++' | tr '\n' ' ')"
[ -z "$SRV_ROOTS" ] && SRV_ROOTS="/home/toxic"
say "server roots: $SRV_ROOTS"

venv_for() {  # $1=dir -> best python, walking up, else the bridge venv, else python3
  _d="$1"
  while [ "$_d" != "/" ] && [ -n "$_d" ]; do
    for v in "$_d/.awrawr-mcp-venv/bin/python" "$_d/venv/bin/python" "$_d/.venv/bin/python"; do
      [ -x "$v" ] && { printf '%s' "$v"; return 0; }
    done
    _d="$(dirname "$_d")"
  done
  _v="$(ls -d /home/*/.awrawr-mcp-venv/bin/python 2>/dev/null | head -1)"
  [ -n "$_v" ] && { printf '%s' "$_v"; return 0; }
  printf 'python3'
}

# --- 4b. v3 confidence-gated server discovery ---------------------------------------
# v2 grepped for the port digits and started the first .py hit — on the real
# box that matched a numpy test file. v3 requires evidence the file IS the
# server before anything is ever started.
_confident_server() {  # $1=file $2=port -> 0 if the file plausibly binds the port
  _f="$1" _port="$2"
  # (a) hard exclusions — never start anything under these
  case "$_f" in
    */venv/*|*/.venv/*|*/site-packages/*|*/node_modules/*|*/.cache/*|*/tests/*|*archive*|*backup*)
      return 1 ;;
    *test_*.py|*_test.py)
      return 1 ;;
  esac
  [ -f "$_f" ] || return 1
  # (b) require a server marker AND a port mention. Neither alone is enough:
  # a marker alone could be any server, a port substring alone could be a
  # test, a comment, or a pid. Both together are the confidence.
  grep -qE 'start_server|serve_forever|uvicorn|Flask\(|FastAPI\(|http\.server|websockets|asyncio' "$_f" 2>/dev/null || return 1
  grep -qE "['\"]${_port}['\"]|PORT[^=]*=[^#]*${_port}|\b${_port}\b" "$_f" 2>/dev/null || return 1
  return 0
}

_file_running() {  # $1=file -> 0 if a live process cmdline contains the full path
  # capture pgrep output first: piping pgrep straight into grep -F would
  # match grep's own cmdline (it contains the pattern). static text can't.
  _procs="$(pgrep -af . 2>/dev/null)"
  printf '%s' "$_procs" | grep -qF -- "$1"
}

find_server_candidates() {  # $1=port -> up to 3 confident .py paths, one per line
  _port="$1" _seen="" _count=0
  _emit() {
    case "$_seen" in *"|$1|"*) return 0 ;; esac
    _seen="${_seen}|$1|"
    _confident_server "$1" "$_port" || return 0
    printf '%s\n' "$1"
    _count=$((_count + 1))
  }
  # (c) preference order: running-process cwds first (SRV_ROOTS is already in
  # that order), top-level .py then */bin/*.py of each root.
  for _r in $SRV_ROOTS; do
    [ -d "$_r" ] || continue
    [ "$_count" -ge 3 ] && break
    for _f in "$_r"/*.py "$_r"/bin/*.py; do
      [ -f "$_f" ] || continue
      _emit "$_f"
      [ "$_count" -ge 3 ] && break
    done
  done
  # deeper grep fallback, junk trees pruned out of the search itself
  if [ "$_count" -lt 3 ] && have rg && have timeout; then
    _hits="$(timeout 45 rg --hidden --no-ignore -l -g '*.py' \
      -g '!**/venv/**' -g '!venv/**' -g '!**/.venv/**' -g '!.venv/**' \
      -g '!**/site-packages/**' -g '!**/node_modules/**' -g '!**/.cache/**' \
      -g '!**/tests/**' -g '!*test_*.py' -g '!*_test.py' \
      -g '!**/archive*/**' -g '!**/backup*/**' -g '!**/.worktree*/**' \
      -g '!**/uv/**' -g '!**/npm/**' \
      -e "\b${_port}\b" $SRV_ROOTS 2>/dev/null)"
    while IFS= read -r _f; do
      [ -n "$_f" ] || continue
      [ "$_count" -ge 3 ] && break
      _emit "$_f"
    done <<EOF
$_hits
EOF
  fi
}

is_squawk() {  # $1=text -> 0 if squawk-related (hands off)
  printf '%s' "$1" | grep -qi 'squawk'
}

start_server_file() {  # $1=file $2=port -> 0 if listening afterwards
  _file="$1" _port="$2"
  _dir="$(dirname "$_file")"
  _py="$(venv_for "$_dir")"
  _log="$_dir/server-restart.log"
  # stale pidfile? if the pid is alive we do NOT start a second copy
  for _pf in "$_dir"/*.pid; do
    [ -f "$_pf" ] || continue
    _ppid="$(cat "$_pf" 2>/dev/null | tr -dc '0-9')"
    if [ -n "$_ppid" ] && kill -0 "$_ppid" 2>/dev/null; then
      _pcmd="$(tr '\0' ' ' < "/proc/$_ppid/cmdline" 2>/dev/null)"
      case "$_pcmd" in *"$(basename "$_file")"*)
        say "  pidfile $_pf -> pid $_ppid alive for $(basename "$_file") — not starting a duplicate"
        return 1 ;; esac
    fi
  done
  say "starting $(basename "$_file") for port $_port: $_py $_file (log: $_log)"
  if [ "$DRYRUN" -eq 1 ]; then
    say "[dry-run] would run: cd $_dir && setsid $_py $_file >>$_log 2>&1 &"
    return 1
  fi
  ( cd "$_dir" && setsid "$_py" "$_file" >>"$_log" 2>&1 < /dev/null & )
  disown 2>/dev/null || true
  for _ in $(seq 1 12); do port_listening "$_port" && return 0; sleep 1; done
  say "  still not listening on $_port — see $_log"
  return 1
}

# --- 5. per-backend health + repair --------------------------------------------------
# For every route in the serve map: port listening? If not, gather up to 3
# confident server candidates and try them in preference order. Squawk
# processes are never killed: a live squawk pid is reported, never touched.
_TRIED_FILES=""
while IFS=$'\t' read -r host path proxy; do
  [ -z "$host" ] || [ "$host" = "ERR" ] && continue
  [ -z "$proxy" ] && { note warn "backend:$path" "no proxy target in serve map"; continue; }
  _port="$(port_of "$proxy")"
  [ -z "$_port" ] && { note warn "backend:$path" "could not parse port from $proxy"; continue; }
  if port_listening "$_port"; then
    note ok "backend:$path" "port $_port listening ($(listener_of "$_port"))"
    continue
  fi
  say "backend $path (port $_port) DOWN — discovering server..."
  _cands="$(find_server_candidates "$_port")"
  if [ -z "$_cands" ]; then
    # (d) REPORT-AND-SKIP: no confident candidate -> print and move on.
    note warn "backend:$path" "no confident server for port $_port — not starting anything"
    continue
  fi
  _started=0 _hands_off=0
  while IFS= read -r _srvfile; do
    [ -n "$_srvfile" ] || continue
    # (e) never attempt the same file twice in one run
    case "$_TRIED_FILES" in *"|$_srvfile|"*)
      say "  already attempted $_srvfile this run — skipping"; continue ;; esac
    # (e) never start a file that's already running
    if _file_running "$_srvfile"; then
      say "  $_srvfile already has a live process — not starting a duplicate"
      _TRIED_FILES="${_TRIED_FILES}|$_srvfile|"
      continue
    fi
    say "  candidate server: $_srvfile"
    if is_squawk "$_srvfile"; then
      # squawk: only start if nothing squawk-ish is alive; never kill.
      _alive="$(pgrep -af '[s]quawk' 2>/dev/null | head -3)"
      if [ -n "$_alive" ]; then
        note warn "backend:$path" "port $_port down but squawk process alive — hands off (needs manual look): $(printf '%s' "$_alive" | head -1 | cut -c1-100)"
        _TRIED_FILES="${_TRIED_FILES}|$_srvfile|"
        _hands_off=1
        break
      fi
      say "  no live squawk process — safe to start $_srvfile"
    else
      # non-squawk: if a stale process for this exact file exists but isn't
      # listening, retire that one pid before starting fresh.
      _stem="$(basename "$_srvfile")"
      for _p in $(pgrep -f "\[$(printf '%s' "$_stem" | cut -c1-1)\]$(printf '%s' "$_stem" | cut -c2-)" 2>/dev/null); do
        _c="$(tr '\0' ' ' < "/proc/$_p/cmdline" 2>/dev/null)"
        case "$_c" in *"$_srvfile"*)
          say "  stale pid $_p for $_stem (not listening) — SIGTERM"
          if run kill "$_p" 2>/dev/null; then
            for _ in $(seq 1 8); do kill -0 "$_p" 2>/dev/null || break; sleep 1; done
            kill -0 "$_p" 2>/dev/null && run kill -9 "$_p" 2>/dev/null
          fi ;;
        esac
      done
    fi
    _TRIED_FILES="${_TRIED_FILES}|$_srvfile|"
    if start_server_file "$_srvfile" "$_port"; then
      note fixed "backend:$path" "started $(basename "$_srvfile"), port $_port now listening"
      _started=1; break
    elif [ "$DRYRUN" -eq 1 ]; then
      note ok "backend:$path" "dry-run: would start $(basename "$_srvfile") for port $_port"
      _started=1; break
    else
      note warn "backend:$path" "candidate $(basename "$_srvfile") failed — trying next"
    fi
  done <<EOF
$_cands
EOF
  [ "$_started" -eq 0 ] && [ "$_hands_off" -eq 0 ] \
    && note fail "backend:$path" "no candidate started a listener on port $_port"
done <<< "$ROUTES_TSV"

# --- 6. systemd units (non-squawk only) ----------------------------------------------
# A unit is only restarted when its backend is still down afterwards; squawk
# units are reported, never restarted (a restart would kill squawk).
if have systemctl; then
  UNITS="$(systemctl list-units --all --no-legend --no-pager 2>/dev/null | grep -iE 'mcp|awrawr' | awk '{print $1}')"
  for u in $UNITS; do
    if is_squawk "$u"; then
      note warn "unit:$u" "squawk unit — reported only, never auto-restarted"
      continue
    fi
    if systemctl is-active --quiet "$u" 2>/dev/null; then
      note ok "unit:$u" "active"
    else
      if run systemctl restart "$u" 2>/dev/null && { [ "$DRYRUN" -eq 1 ] || systemctl is-active --quiet "$u"; }; then
        note fixed "unit:$u" "restarted"
      else note fail "unit:$u" "restart failed (journalctl -u $u -n 50)"; fi
    fi
  done
fi

# --- 7. deploy hatch-side client files (gist ONLY) ------------------------------------
# exec.py / ws_daemon.py run on HATCH, not yote — this just keeps the checkout
# in sync. v1's raw.githubusercontent.com/toxicwind/gear fallback is dead
# (no such repo); the gist mirror is the only source.
YF_CACHE="/var/cache/yote-fix/bridge-dir"
if [ -z "$BRIDGE_DIR" ] && [ -f "$YF_CACHE" ]; then
  _cached="$(cat "$YF_CACHE" 2>/dev/null)"
  [ -n "$_cached" ] && [ -f "$_cached/exec.py" ] && BRIDGE_DIR="$_cached"
fi
if [ -z "$BRIDGE_DIR" ]; then
  if have rg && have timeout; then
    _found="$(timeout 25 rg --hidden --no-ignore --files -g '!proc/**' -g '!sys/**' \
      -g '!dev/**' -g '!run/**' /home /opt /srv /root /usr/local 2>/dev/null \
      | grep 'awrawr-mcp/bin/exec\.py$' | head -1)"
  fi
  [ -z "${_found:-}" ] && _found="$(timeout 25 find /home /opt /srv /root /usr/local \
    -path /proc -prune -o -type f -path '*awrawr-mcp/bin/exec.py' -print 2>/dev/null | head -1)"
  [ -n "${_found:-}" ] && BRIDGE_DIR="$(dirname "$_found")"
  if [ -n "${BRIDGE_DIR:-}" ]; then
    mkdir -p "$(dirname "$YF_CACHE")" 2>/dev/null
    echo "$BRIDGE_DIR" > "$YF_CACHE" 2>/dev/null
  fi
fi
GIST_RAW="https://gist.githubusercontent.com/toxicwind/e817e044162bb59c386615f89b1baeb0/raw"
if [ -n "${BRIDGE_DIR:-}" ] && [ -d "$BRIDGE_DIR" ] && have curl; then
  note ok "deploy:dir" "$BRIDGE_DIR"
  for f in exec.py ws_daemon.py; do
    _tmp="$(mktemp)"; _got=0
    if curl -sSL --fail --max-time 30 -o "$_tmp" "$GIST_RAW/$f" 2>/dev/null \
       && python3 -m py_compile "$_tmp" 2>/dev/null; then _got=1; fi
    if [ "$_got" -eq 0 ]; then
      note fail "deploy:$f" "gist download/compile check failed"; rm -f "$_tmp"; continue
    fi
    if [ -f "$BRIDGE_DIR/$f" ] && cmp -s "$_tmp" "$BRIDGE_DIR/$f"; then
      note ok "deploy:$f" "already current"
    else
      [ -f "$BRIDGE_DIR/$f" ] && run cp -p "$BRIDGE_DIR/$f" "$BRIDGE_DIR/$f.bak-$TS"
      if run bash -c "cat \"\$0\" > \"\$1\"" "$_tmp" "$BRIDGE_DIR/$f"; then
        note fixed "deploy:$f" "installed from gist"
      else note fail "deploy:$f" "install failed"; fi
    fi
    rm -f "$_tmp"
  done
else
  note warn "deploy" "no awrawr-mcp/bin dir found — skipping client-file sync (server repair above is unaffected)"
fi

# --- 8. verify: 443 listener (tailscaled/Funnel is EXPECTED here) ----------------------
if have ss; then
  L443="$(ss -tlnp 2>/dev/null | awk '$4 ~ /:443$/')"
  if [ -z "$L443" ]; then
    note fail "verify:443" "nothing listening on TCP/443"
  else
    LPID="$(printf '%s' "$L443" | grep -oE 'pid=[0-9]+' | head -1 | cut -d= -f2)"
    LNAME="$(tr '\0' ' ' < "/proc/$LPID/cmdline" 2>/dev/null | cut -c1-60)"
    case "$LNAME" in *tailscaled*)
      note ok "verify:443" "tailscaled (Funnel) on 443 — expected" ;;
      *) note warn "verify:443" "443 held by pid ${LPID:-?}: ${LNAME:-unidentified} (expected tailscaled)" ;;
    esac
  fi
else note warn "verify:443" "ss missing — skipping"; fi

# --- 9. verify: per-route HTTPS probes (tailnet DNS = correct SNI) ---------------------
# Any HTTP answer (even 400/404/426 on websocket paths) proves TLS+route alive.
# 502 = listener up, backend down. 000 = connection/TLS failure.
while IFS=$'\t' read -r host path proxy; do
  [ -z "$host" ] || [ "$host" = "ERR" ] && continue
  _code="$(curl -sk -o /dev/null -w '%{http_code}' --max-time 8 "https://${TAILNAME}${path}" 2>/dev/null || true)"
  _code="${_code:0:3}"
  case "$_code" in
    502) note fail "verify:$path" "HTTP 502 — route up, backend down" ;;
    000|"") note fail "verify:$path" "connection failed (TLS/route)" ;;
    *)   note ok "verify:$path" "HTTP $_code via $TAILNAME" ;;
  esac
done <<< "$ROUTES_TSV"

# --- 10. verify: authenticated WSS handshake on /exec-ws ---------------------------------
# TLS to the tailnet name (correct SNI) + the token from disk. Expect HTTP 101.
# A 401 means the token on disk is not what the bridge expects.
if [ -n "${TOKEN:-}" ] && [ -f "$TOKEN" ]; then
  WS_RESULT="$(TOKEN_PATH="$TOKEN" TAIL_NAME="$TAILNAME" python3 - 2>/dev/null <<'PYEOF'
import socket, ssl, base64, os
tok = open(os.environ["TOKEN_PATH"]).read().strip()
host = os.environ["TAIL_NAME"]
try:
    s = socket.create_connection((host, 443), timeout=10)
    ctx = ssl.create_default_context(); ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    s = ctx.wrap_socket(s, server_hostname=host)   # SNI = tailnet name, never the IP
    key = base64.b64encode(os.urandom(16)).decode()
    req = ("GET /exec-ws HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\n"
           "Connection: Upgrade\r\nSec-WebSocket-Key: %s\r\n"
           "Sec-WebSocket-Version: 13\r\nX-MCP-Token: %s\r\n\r\n" % (host, key, tok))
    s.sendall(req.encode())
    print(s.recv(1024).decode("latin1", "replace").split("\r\n", 1)[0])
except Exception as e:
    print("ERROR " + str(e)[:80])
PYEOF
)"
  case "$WS_RESULT" in
    *" 101 "*) note ok "verify:exec-ws-wss" "HTTP 101 — bridge accepted the token, WSS alive" ;;
    *" 401"*)  note fail "verify:exec-ws-wss" "HTTP 401 — token on disk rejected (fp above)" ;;
    "ERROR"*)  note fail "verify:exec-ws-wss" "TCP/TLS failed: ${WS_RESULT#ERROR }" ;;
    "")        note fail "verify:exec-ws-wss" "empty response" ;;
    *)         note warn "verify:exec-ws-wss" "unexpected: $WS_RESULT" ;;
  esac
else note warn "verify:exec-ws-wss" "need token file — skipping"; fi

# --- 11. --supervise: unit for the DISCOVERED exec-ws server (never exec.py) ---------------
if [ "$SUPERVISE" -eq 1 ]; then
  _execws_port="$(printf '%s' "$ROUTES_TSV" | awk -F'\t' '$2=="/exec-ws"{print $3}' | sed -n 's#.*:\([0-9]*\).*#\1#p')"
  _srv="$(find_server_candidates "${_execws_port:-8379}" | head -1)"
  if [ -n "$_srv" ] && ! is_squawk "$_srv"; then
    _dir="$(dirname "$_srv")"; _py="$(venv_for "$_dir")"
    BUSER="${SUDO_USER:-toxic}"
    UNIT=/etc/systemd/system/awrawr-ws-exec.service
    if [ "$DRYRUN" -eq 1 ]; then
      say "[dry-run] would write $UNIT (User=$BUSER, ExecStart=$_py $_srv) + enable --now"
      note fixed "supervise" "dry-run unit planned for $(basename "$_srv")"
    else
      cat > "$UNIT" <<EOF
[Unit]
Description=awrawr ws exec server ($(basename "$_srv"))
After=network-online.target tailscaled.service
Wants=network-online.target

[Service]
Type=simple
User=$BUSER
WorkingDirectory=$_dir
ExecStart=$_py $_srv
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
      if systemctl daemon-reload && systemctl enable --now awrawr-ws-exec.service; then
        note fixed "supervise" "unit installed for $(basename "$_srv") ($UNIT)"
      else note fail "supervise" "unit written but enable/start failed"; fi
    fi
  else note fail "supervise" "no non-squawk /exec-ws server file discovered — nothing to supervise"; fi
fi

# --- report ----------------------------------------------------------------------------------
printf 'yote-fix v3  tailnet=%s dry_run=%s\n' "$TAILNAME" "$DRYRUN"
printf '%-6s %-18s %s\n' "STATUS" "CHECK" "DETAIL"
while IFS='|' read -r st name detail; do
  [ -z "$st" ] && continue
  printf '%-6s %-18s %s\n' "$st" "$name" "$detail"
done <<< "$CHECKS"

FAILS="$(printf '%s' "$CHECKS" | grep -c '^fail|' || true)"
[ "$FAILS" -gt 0 ] && exit 1
exit 0
