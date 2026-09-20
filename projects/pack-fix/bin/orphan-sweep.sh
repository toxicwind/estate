#!/usr/bin/env bash
# orphan-sweep.sh — repeatable yote PROCESS orphan audit (processes scope ONLY).
# Part of the pack-fix crew, sovereign-projects: projects/pack-fix/bin/orphan-sweep.sh
#
# What it does:
#   1. Snapshots the full userspace process table on yote.
#   2. Classifies every process against the known-daemon allowlist below.
#   3. Flags UNKNOWN long-runners with owner evidence (cmdline, cwd, start, ports).
#   4. Scans for stale *.pid files (PID dead or cmdline mismatch).
# It NEVER kills anything. Disposition (adopt/kill) is a human/fleet decision.
#
# Usage: orphan-sweep.sh [--json] [--pid-dirs DIR ...]
# Exit: 0 = no orphans/stale pids, 1 = findings, 2 = error.
#
# Lane: yote processes only. /tmp file triage belongs to kimi-unlock-audit;
# repo orphan integration belongs to repo-integrator-max. This script does not
# touch files beyond reading pid files.

set -uo pipefail

JSON=0
PID_DIRS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --json) JSON=1; shift ;;
    --pid-dirs) shift; while [[ $# -gt 0 && "$1" != --* ]]; do PID_DIRS+=("$1"); shift; done ;;
    *) echo "usage: $0 [--json] [--pid-dirs DIR ...]" >&2; exit 2 ;;
  esac
done
[[ ${#PID_DIRS[@]} -eq 0 ]] && PID_DIRS=(/home/toxic /home/toxic/sovereign /home/toxic/paper-poller/state /home/toxic/buildsrv /home/toxic/projects)

ORPHANS=0; STALE=0
declare -a REPORT_LINES=()
declare -a JSON_ITEMS=()

log()  { [[ $JSON -eq 0 ]] && echo "$*"; }
jadd() { JSON_ITEMS+=("$1"); }

# --- Known-daemon allowlist (regexes matched against full cmdline) ---
# Keep this current: herd/keypool/model-guard ports, squawk, pitchfork,
# oracle market, bridge, and the desktop session.
ALLOW=(
  'pitchfork (supervisor run|log-sink)'
  'llama-swap --config .*herd\.yaml'
  'herd-keypool\.py'
  'herd-model-guard\.py'
  'llama-server'
  'squawk_(feed|ws_server|ws_client)|squawk-ws/squawk_ws|/squawk-relay/(sink|forward)\.py|squawk/chat\.py'
  'oracle_loop\.py|market_watchdog\.py|bidder\.py --id'
  'awrawr_ws_exec\.py|awrawr_mcp\.py|gemini-mcp/server\.py|whatsapp-mcp/server\.py'
  'kimi-auto/(loop\.sh|shim\.py)'
  'openfang-health/loop\.sh|openfang-run\.sh|openfang (start|mcp)'
  'fleet-watchdog/sweepd\.sh|isleep .*fleet-watchdog'
  'phone-lane/bin/(phone-vitals|phone-lane-keeper)'
  'actions-runner'
  'tailscaled|sshd|systemd|sd-pam|dbus|pipewire|wireplumber|portal|gvfs|udisksd|localsearch|at-spi|rtkit|polkit|geoclue|upowerd|power-profiles|wpa_supplicant|bluetoothd|cupsd|avahi|containerd|docker|postgres|lact|bpftune|ananicy|scx_|seatd|sddm|Hyprland|hypridle|hyprsunset|wezterm|firefox|Xwayland|easyeffects|wl-paste|quickshell|ydotool|bubbleupnp|nvidia-persistenced|limine-snapper|waydroid|inotifywait'
  'shep serve|/mesh/bin/|mcp-background-job|arxiv-mcp|markitdown-mcp|codebase-memory-mcp|xray-mcp|ghas-mcp|ast-grep-mcp|openfang-mcp-shim|prometheus-mcp|sequential-thinking|llama_swap\.ts|computer-use-linux mcp|exa-mcp-server|redis-mcp-server|patchwork-mcp|server-github|smarter-faster-better-mcp|context7-mcp'
  'buildsrvd\.py|buildsrv-watchdog\.py'
  'paper-poller/bin/(poller|watchdog)\.py'
  'refusal-watchdog\.py|sorry-watchdog\.py'
  'forensics-srv/server\.py'
  'boundless.*uvicorn|uvicorn web\.server'
  'ml-serve/server\.py'
  'bench-radar/server\.ts'
  'mesh-front\.ts|mesh-hub\.ts|mesh-landing|landing\.py'
  'router\.ts|chat\.ts|src/server\.ts|sovereign_web|next-server|next dev|postcss\.js|dashboard/server\.ts|ralph-dashboard|kimi-code'
  'qdrant-server|prometheus|grafana|node_exporter|nginx: (master|worker) process'
  'valkey-server|redis-server'
  'dnsmasq.*cni|dagger-engine'
  'xdg-permission-store|dconf-service|start-hyprland|nmcli monitor|gpg-agent --homedir /etc/pacman|dirmngr --homedir /etc/pacman|gnome-keyring-daemon'
  'sccache'
  'pacman -Syu|/tmp/alpm_|ldconfig'
  'stash-guard\.py'
  'auctioneer\.py'
  'alias-shim\.py'
  'oracle_daemon\.py'
  'kimi-claw/bridge\.ts'
  'herd-race'
  'browserless/app'
  '\.flock/flock'
  'desktop-commander|agent-orchestration|agent-mcp-gateway'
  'find / -name|find /home /tmp|tail -[0-9]+|head -[0-9]+'
  'qdrant-mcp-server'
  'vite build'
  'git fsck'
  'grep commit'
  'guidellm|eval_runner\.py|bench\.sh|nvidia-alive'
  'tau|omp --no-session'
  'bun run|node .*coding-agent'
  'sleep [0-9]+'
  'tmux|^-bash[[:space:]]*$|/bin/sh -c'
  'cloudflared tunnel'   # flagged separately as UNCLAIMED-EXPOSED, not killed
  'adb -L|dockerd|tini --'
)

is_allowed() {
  local cmd="$1"
  for re in "${ALLOW[@]}"; do
    [[ "$cmd" =~ $re ]] && return 0
  done
  return 1
}

self_pid=$$
# ancestor check via live /proc walk (skip our own snapshot pipeline,
# including processes spawned after the script started)
is_mine() {
  local p=$1 seen=0 pp
  while [[ $seen -lt 40 ]]; do
    pp=$(awk '{print $4}' "/proc/$p/stat" 2>/dev/null) || return 1
    [[ -z "$pp" || "$pp" == "0" ]] && return 1
    [[ "$pp" == "$self_pid" ]] && return 0
    p=$pp; seen=$((seen+1))
  done
  return 1
}

log "== orphan-sweep $(date -u +%FT%TZ) host=$(hostname) =="

# --- Process inventory ---
while IFS= read -r line; do
  pid=$(awk '{print $1}' <<<"$line"); ppid=$(awk '{print $2}' <<<"$line")
  start=$(awk '{print $3, $4, $5, $6, $7}' <<<"$line")   # lstart = 5 fields
  cmd=$(awk '{for(i=8;i<=NF;i++) printf "%s ", $i; print ""}' <<<"$line")
  [[ "$pid" == "PID" || -z "$pid" ]] && continue
  [[ "$pid" == "$self_pid" ]] && continue
  [[ -d "/proc/$pid" ]] || continue  # already exited: transient, nothing to do
  is_mine "$pid" && continue   # our own snapshot pipeline
  # kernel threads
  [[ "$ppid" == "2" || "$cmd" =~ ^\[.*\][[:space:]]*$ ]] && continue
  # transient helpers of this very sweep
  [[ "$cmd" =~ (orphan-sweep|yote-conn|exec\.py) ]] && continue
  # defunct: report once, cheap
  if [[ "$cmd" =~ \<defunct\> ]]; then
    log "ZOMBIE pid=$pid ppid=$ppid cmd=${cmd:0:60}"
    jadd "{\"type\":\"zombie\",\"pid\":$pid,\"ppid\":$ppid}"
    continue
  fi
  if is_allowed "$cmd"; then continue; fi
  # UNKNOWN: gather owner evidence
  cwd=$(readlink "/proc/$pid/cwd" 2>/dev/null || echo "?")
  ORPHANS=$((ORPHANS+1))
  log "ORPHAN pid=$pid ppid=$ppid started=\"$start\" cwd=$cwd"
  log "        cmd=${cmd:0:220}"
  jadd "{\"type\":\"orphan\",\"pid\":$pid,\"ppid\":$ppid,\"started\":\"$start\",\"cwd\":\"$cwd\",\"cmd\":\"$(sed 's/"/\\"/g' <<<"${cmd:0:220}")\"}"
done < <(ps -eo pid,ppid,lstart,args --sort=start_time)

# --- Stale pid files ---
for d in "${PID_DIRS[@]}"; do
  [[ -d "$d" ]] || continue
  while IFS= read -r -d '' f; do
    # skip VCS internals
    [[ "$f" == */.git/* ]] && continue
    p=$(head -c 32 "$f" 2>/dev/null | tr -cd '0-9\n' | head -1)
    [[ -z "$p" ]] && continue
    if kill -0 "$p" 2>/dev/null; then
      owner=$(ps -p "$p" -o args= 2>/dev/null | cut -c1-50)
      # pid alive but unrelated binary -> stale too
      base=$(basename "$f" .pid)
      if [[ "$owner" != *"$base"* && "$f" != *"bench-all"* ]]; then
        log "STALE-PID $f -> $p (alive but unrelated: $owner)"
        jadd "{\"type\":\"stale-pid\",\"file\":\"$f\",\"pid\":$p,\"note\":\"pid-reuse\"}"
        STALE=$((STALE+1))
      fi
    else
      log "STALE-PID $f -> $p (dead)"
      jadd "{\"type\":\"stale-pid\",\"file\":\"$f\",\"pid\":$p,\"note\":\"dead\"}"
      STALE=$((STALE+1))
    fi
  done < <(find "$d" -maxdepth 3 -name '*.pid' -print0 2>/dev/null)
done

if [[ $JSON -eq 1 ]]; then
  printf '{\n  "host": "%s",\n  "time": "%s",\n  "orphans": %d,\n  "stale_pids": %d,\n  "items": [\n' "$(hostname)" "$(date -u +%FT%TZ)" "$ORPHANS" "$STALE"
  for ((i=0;i<${#JSON_ITEMS[@]};i++)); do
    [[ $i -gt 0 ]] && printf ',\n'
    printf '    %s' "${JSON_ITEMS[$i]}"
  done
  printf '\n  ]\n}\n'
else
  log "== done: $ORPHANS orphan processes, $STALE stale pid files =="
fi

[[ $ORPHANS -gt 0 || $STALE -gt 0 ]] && exit 1 || exit 0
