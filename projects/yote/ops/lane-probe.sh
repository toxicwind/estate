#!/usr/bin/env bash
# lane-probe.sh — Tailscale funnel lane health probe (corrected 2026-09-20)
#
# Probes every funnel path the way outside traffic sees it: dial the TAILNET
# IP on 443 with correct SNI. Never 127.0.0.1:443 — funnel binds 443 on the
# tailnet IPs only, so a localhost:443 probe gets connection-refused on every
# path and looks exactly like a total wedge. That false positive once caused
# an unnecessary tailscaled restart. This script refuses to repeat it:
#   1. resolves the tailnet IP itself via `tailscale ip -4`
#   2. verifies TCP 443 reachability BEFORE probing any path
#   3. only calls it a wedge when TCP+TLS succeed but HTTP gets nothing
# A 401 from /exec-ws or /mcp means transport+app alive (auth layer
# responding) and counts as healthy.
#
# Usage: lane-probe.sh [--repair]
#   --repair  on a REAL all-paths wedge only: restart tailscaled, verify the
#             serve map is intact, and re-probe. Without it: report only.
# Exit: 0 all healthy | 1 degraded or real wedge | 2 probe broken

set -u

TS_DNS="${TS_DNS:-github-mcp-host.tailc9ac71.ts.net}"
WANT_REPAIR=0
[[ "${1:-}" == "--repair" ]] && WANT_REPAIR=1

log() { printf '%s\n' "$*"; }

tail_ip="$(tailscale ip -4 2>/dev/null | head -n 1)"
if [[ -z "$tail_ip" ]]; then
    log "PROBE BROKEN: 'tailscale ip -4' returned nothing — is tailscaled running?"
    exit 2
fi
log "tailnet ip: $tail_ip   SNI: $TS_DNS"

if ! timeout 8 bash -c "</dev/tcp/$tail_ip/443" 2>/dev/null; then
    log "PROBE BROKEN: TCP $tail_ip:443 unreachable."
    log "Check: systemctl is-active tailscaled ; ss -ltn | grep ':443 '"
    log "Note: funnel binds 443 on tailnet IPs only — never probe 127.0.0.1:443."
    exit 2
fi
log "TCP $tail_ip:443 reachable"

serve_paths() {
    timeout 15 sudo tailscale serve status 2>/dev/null \
        | grep -oE '\|-- /[^ ]*' | awk '{print $2}' | sort -u
}
serve_map_sig() {
    timeout 15 sudo tailscale serve status 2>/dev/null \
        | grep -oE '\|-- /[^ ]* +proxy' | sort
}

declare -A CODE
probe_path() {
    local path="$1" code
    if [[ "$path" == "/exec-ws" ]]; then
        code=$(curl -sk -o /dev/null -w "%{http_code}" -m 10 \
            --resolve "$TS_DNS:443:$tail_ip" "https://$TS_DNS$path" \
            -H "Connection: Upgrade" -H "Upgrade: websocket" \
            -H "Sec-WebSocket-Version: 13" \
            -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" 2>/dev/null)
    else
        code=$(curl -sk -o /dev/null -w "%{http_code}" -m 10 \
            --resolve "$TS_DNS:443:$tail_ip" "https://$TS_DNS$path" 2>/dev/null)
    fi
    CODE["$path"]="${code:-000}"
    log "funnel $path -> HTTP ${CODE[$path]}"
}

mapfile -t PATHS < <(serve_paths)
if [[ "${#PATHS[@]}" -eq 0 ]]; then
    log "PROBE BROKEN: no funnel paths parsed from 'tailscale serve status'."
    exit 2
fi

for p in "${PATHS[@]}"; do
    probe_path "$p"
done

total="${#PATHS[@]}"
dead=0
sick=()
for p in "${PATHS[@]}"; do
    if [[ "${CODE[$p]:-000}" == "000" ]]; then
        dead=$((dead + 1))
        sick+=("$p")
    fi
done
log "paths: $total dead: $dead"

if [[ "$dead" -eq 0 ]]; then
    log "VERDICT: all funnel paths alive (TCP+TLS+HTTP via tailnet $tail_ip)"
    exit 0
fi

if [[ "$dead" -lt "$total" ]]; then
    log "VERDICT: DEGRADED — dead paths: ${sick[*]}"
    log "(000 after TCP 443 succeeded = TLS accepted but backend gave no HTTP)"
    exit 1
fi

# All paths 000 with TCP 443 reachable: a real wedge, not a probe artifact.
log "VERDICT: REAL WEDGE — TCP $tail_ip:443 ok, TLS up, zero HTTP responses."
if [[ "$WANT_REPAIR" -ne 1 ]]; then
    log "Rerun with --repair to restart tailscaled and re-probe."
    exit 1
fi

log "--- restarting tailscaled (--repair) ---"
map_before="$(serve_map_sig)"
journalctl -u tailscaled --since "30 min ago" -p err 2>/dev/null | tail -10
sudo systemctl restart tailscaled
for _ in $(seq 1 30); do
    timeout 2 bash -c "</dev/tcp/$tail_ip/443" 2>/dev/null && break
    sleep 2
done
if ! timeout 8 bash -c "</dev/tcp/$tail_ip/443" 2>/dev/null; then
    log "!!! 443 STILL DOWN after tailscaled restart — manual intervention needed"
    exit 1
fi
log "443 back"
map_after="$(serve_map_sig)"
if [[ "$map_before" == "$map_after" ]]; then
    log "serve map INTACT across restart"
else
    log "!!! SERVE MAP CHANGED across restart — inspect manually"
    diff <(printf '%s\n' "$map_before") <(printf '%s\n' "$map_after") || true
fi

log "--- re-probe ---"
dead=0
for p in "${PATHS[@]}"; do
    probe_path "$p"
    [[ "${CODE[$p]:-000}" == "000" ]] && dead=$((dead + 1))
done
log "paths: $total dead after repair: $dead"
[[ "$dead" -eq 0 ]] && exit 0 || exit 1
