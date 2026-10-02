#!/usr/bin/env bash
# herd-status.sh — one-shot herd runtime health dashboard (runs on yote).
# Shows: live herd processes, pitchfork daemon states, port health,
# recent log errors, config sanity (live vs SSOT), staleness signals.
# Exit: 0 = healthy, 1 = warnings, 2 = critical.
set -u
SOV=/home/toxic/sovereign
WS=$SOV/shingle-workspace
PF=/home/toxic/.local/share/mise/installs/pitchfork/2.25.0/pitchfork
CRIT=0
WARN=0

hdr()  { printf '\n=== %s ===\n' "$1"; }
ok()   { printf '  [ok]   %s\n' "$1"; }
warn() { printf '  [warn] %s\n' "$1"; WARN=1; }
crit() { printf '  [CRIT] %s\n' "$1"; CRIT=1; }
info() { printf '  %s\n' "$1"; }

# ---- SSOT ports -----------------------------------------------------------
HERD_PORT=$(grep -E '^HERD_PORT=' $SOV/config/ports.env 2>/dev/null | cut -d= -f2)
BEELLAMA_PORT=$(grep -E '^BEELLAMA_PORT=' $SOV/config/ports.env 2>/dev/null | cut -d= -f2)
HERD_PORT=${HERD_PORT:-25100}
BEELLAMA_PORT=${BEELLAMA_PORT:-25122}
info "SSOT ports: herd=$HERD_PORT beellama-fast=$BEELLAMA_PORT (config/ports.env)"

# ---- 1. live processes ------------------------------------------------------
hdr "1. LIVE HERD PROCESSES"
SWAP_PIDS=$(pgrep -f 'llama-swap.*herd\.yaml' || true)
FAST_PIDS=$(pgrep -f 'beellama.*llama-server' || true)
if [ -z "$SWAP_PIDS" ]; then
  crit "llama-swap (herd gateway) NOT running"
else
  for p in $SWAP_PIDS; do
    et=$(ps -o etime= -p "$p" 2>/dev/null | tr -d ' ')
    cmd=$(tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null | cut -c1-160)
    ok "llama-swap pid=$p uptime=$et"
    info "       $cmd"
  done
fi
if [ -z "$FAST_PIDS" ]; then
  warn "beellama-fast (llama-server) NOT running"
else
  for p in $FAST_PIDS; do
    et=$(ps -o etime= -p "$p" 2>/dev/null | tr -d ' ')
    ppid=$(ps -o ppid= -p "$p" 2>/dev/null | tr -d ' ')
    fport=$(tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null | grep -oE -- '--port [0-9]+' | awk '{print $2}')
    alias=$(tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null | grep -oE -- '--alias [^ ]+' | awk '{print $2}')
    mgr="llama-swap-managed"; [ "$ppid" = "1006" ] && mgr="pitchfork-managed"
    ok "beellama pid=$p port=${fport:-?} alias=${alias:-none} uptime=$et ($mgr)"
  done
fi

# ---- 2. pitchfork daemons ---------------------------------------------------
hdr "2. PITCHFORK DAEMONS (herd slice)"
if ! systemctl --user is-active --quiet pitchfork.service 2>/dev/null; then
  crit "pitchfork.service not active"
else
  ok "pitchfork.service active"
fi
# NOTE: pitchfork CLI must run from the config dir or it reports stale states
PF_LIST=$(cd $SOV && $PF list 2>/dev/null | grep -iE 'herd|beellama' || true)
if [ -z "$PF_LIST" ]; then
  warn "no herd/beellama daemons found in pitchfork list"
else
  echo "$PF_LIST" | while read -r name state rest; do
    case "$state" in
      running|available) printf '  [ok]   %-32s %s\n' "$name" "$state" ;;
      *)                 printf '  [info] %-32s %s (reconciling below)\n' "$name" "$state" ;;
    esac
  done
  echo "$PF_LIST" | grep -qE ' (errored|stopped|failed) ' || true
  # reconcile supervisor state against reality: an 'errored' daemon whose process is
  # alive and healthy is stale bookkeeping (warn), not an outage (crit)
  while read -r name state rest; do
    [ -z "$name" ] && continue
    alive=0
    case "$name" in
      sovereign/beellama-fast) [ -n "$FAST_PIDS" ] && alive=1 ;;
      sovereign/herd)          [ -n "$SWAP_PIDS" ] && alive=1 ;;
    esac
    if [ "$alive" = "1" ]; then
      warn "$name reports '$state' but its process is alive (stale supervisor bookkeeping?)"
    else
      crit "$name reports '$state' and no live process found"
    fi
  done < <(echo "$PF_LIST" | grep -E ' (errored|stopped|failed) ' || true)
fi

# ---- 3. ports + HTTP health -------------------------------------------------
hdr "3. PORTS + HTTP HEALTH"
probe() { # name port path — retries once; a first-try failure that recovers is a warn (transient)
  # NOTE: keep the two `local` lines separate — bash+set -u rejects $port in the same
  # `local` command that declares it ("port: unbound variable").
  local name="$1" port="$2" path="$3"
  local url="http://127.0.0.1:$port$path"
  local out="" tries=0
  if ! ss -ltn 2>/dev/null | grep -q ":$port "; then
    crit "$name port $port NOT listening"; return
  fi
  while [ $tries -lt 2 ]; do
    if out=$(curl -s -o /dev/null -m 5 -w '%{http_code} %{time_total}' "$url" 2>/dev/null); then
      break
    fi
    tries=$((tries+1)); sleep 1
  done
  local code=$(echo "$out" | awk '{print $1}') tm=$(echo "$out" | awk '{print $2}')
  if [ "$code" = "200" ]; then
    if [ "$tries" -gt 0 ]; then
      warn "$name 127.0.0.1:$port$path -> $code (${tm}s) but needed retry (transient stall)"
    else
      ok "$name 127.0.0.1:$port$path -> $code (${tm}s)"
    fi
  else
    crit "$name 127.0.0.1:$port$path -> ${code:-000} (listening but no HTTP response)"
  fi
}
probe "herd-gateway " "$HERD_PORT" "/health"
probe "beellama-fast" "$BEELLAMA_PORT" "/health"
SERVE_N=$(tailscale serve status 2>/dev/null | grep -c 'http://127.0.0.1' || true)
info "tailscale serve backends: $SERVE_N (herd endpoints are loopback-only by design)"

# ---- 4. recent log errors ----------------------------------------------------
hdr "4. RECENT LOG ERRORS (newest herd logs first)"
LOG_FILES=$(ls -t $SOV/logs/herd-*.log $SOV/data/herd-manual*.log 2>/dev/null || true)
if [ -z "$LOG_FILES" ]; then
  warn "no herd log files found"
else
  found=0
  for f in $LOG_FILES; do
    hits=$(tail -400 "$f" 2>/dev/null | grep -iE 'error|warn|fatal|panic|traceback|bind:' | tail -6)
    if [ -n "$hits" ]; then
      echo "  -- $(basename $f):"
      echo "$hits" | sed 's/^/     /' | cut -c1-150
      found=1
    fi
  done
  [ "$found" = "0" ] && ok "no ERROR/WARN lines in recent tails"
  info "note: logs are historical (manual runs Sep 14-17); live herd logs via pitchfork log-sink"
fi

# ---- 5. config sanity: live vs SSOT ------------------------------------------
hdr "5. CONFIG SANITY (live vs SSOT)"
# live llama-swap cmdline
if [ -n "$SWAP_PIDS" ]; then
  live_cfg=$(tr '\0' '\n' < /proc/$(echo $SWAP_PIDS | cut -d' ' -f1)/cmdline 2>/dev/null | grep -x -A1 -- '--config' | tail -1)
  live_cfgdir=$(tr '\0' '\n' < /proc/$(echo $SWAP_PIDS | cut -d' ' -f1)/cmdline 2>/dev/null | grep -x -A1 -- '--config-dir' | tail -1)
  live_listen=$(tr '\0' ' ' < /proc/$(echo $SWAP_PIDS | cut -d' ' -f1)/cmdline 2>/dev/null | grep -oE -- '--listen [^ ]+' | awk '{print $2}')
  [ -f "$live_cfg" ] && ok "live --config exists: $live_cfg ($(stat -c '%y' "$live_cfg" | cut -d. -f1))" \
                     || crit "live --config MISSING: $live_cfg"
  [ -d "$live_cfgdir" ] && ok "live --config-dir: $live_cfgdir ($(ls "$live_cfgdir" | wc -l) files)" \
                        || warn "live --config-dir missing: $live_cfgdir"
  case "$live_listen" in
    *:$HERD_PORT) ok "live --listen $live_listen matches SSOT HERD_PORT=$HERD_PORT" ;;
    *) warn "live --listen $live_listen != SSOT HERD_PORT=$HERD_PORT" ;;
  esac
fi
if [ -n "$FAST_PIDS" ]; then
  live_fport=$(tr '\0' ' ' < /proc/$(echo $FAST_PIDS | cut -d' ' -f1)/cmdline 2>/dev/null | grep -oE -- '--port [0-9]+' | awk '{print $2}')
  if [ "$live_fport" = "$BEELLAMA_PORT" ]; then
    ok "live beellama --port $live_fport matches SSOT BEELLAMA_PORT"
  else
    warn "live beellama --port $live_fport != SSOT $BEELLAMA_PORT"
  fi
fi
# wrapper script guards (bin + model exist)
for check in "bin:/home/toxic/projects/sovereign-projects/herd/engines/beellama.cpp/build-cuda86/bin/llama-server" \
             "model:/home/toxic/models/EXAONE-4.0-1.2B-IQ4_XS.gguf"; do
  label=${check%%:*}; path=${check#*:}
  [ -e "$path" ] && ok "beellama-fast $label present" || crit "beellama-fast $label MISSING: $path"
done
grep -q '^\[daemons\.herd\]' $SOV/pitchfork.toml && ok "pitchfork.toml [daemons.herd] defined" \
  || warn "pitchfork.toml missing [daemons.herd]"
grep -q '^\[daemons\.beellama-fast\]' $SOV/pitchfork.toml && ok "pitchfork.toml [daemons.beellama-fast] defined" \
  || warn "pitchfork.toml missing [daemons.beellama-fast]"

# ---- 6. staleness signals ----------------------------------------------------
hdr "6. STALENESS SIGNALS"
dead=$(find $WS -xtype l 2>/dev/null | head -10)
if [ -z "$dead" ]; then ok "no dead symlinks in shingle-workspace"; else warn "dead symlinks:"; echo "$dead" | sed 's/^/  /'; fi
litter=$(ls -d $SOV/*-wt-* $SOV/*-17894* $SOV/*-2026091* 2>/dev/null | wc -l)
[ "$litter" -gt 20 ] && warn "worktree litter in sovereign/: $litter stale dirs" \
                     || info "worktree litter in sovereign/: $litter dirs"
scanleft=$(ls -d /home/toxic/herd-scan-* 2>/dev/null | wc -l)
[ "$scanleft" -gt 0 ] && warn "leftover herd-scan clones: $scanleft" || ok "no leftover herd-scan clones"
for d in herd-ci herd-ci-health herd-demote readmefix-herd; do
  if [ -d "$WS/$d" ]; then
    mt=$(stat -c '%y' "$WS/$d" | cut -d' ' -f1)
    info "tooling dir $d mtime=$mt"
  fi
done
python3 -m py_compile $WS/herdscan.py 2>/dev/null && ok "herdscan.py compiles" \
  || warn "herdscan.py syntax issue"

# ---- summary -----------------------------------------------------------------
hdr "SUMMARY"
if [ "$CRIT" -gt 0 ]; then
  echo "  HERD STATUS: CRITICAL"
  exit 2
elif [ "$WARN" -gt 0 ]; then
  echo "  HERD STATUS: DEGRADED (warnings)"
  exit 1
else
  echo "  HERD STATUS: HEALTHY"
  exit 0
fi
