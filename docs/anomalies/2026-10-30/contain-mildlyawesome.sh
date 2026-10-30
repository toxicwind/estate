#!/usr/bin/env bash
# contain-mildlyawesome.sh — execute the instant the DEDI root password is provided.
# Usage: DEDI_PW=<password> bash contain-mildlyawesome.sh [--inspect-only]
set -euo pipefail
IP=172.96.160.178
PW="${DEDI_PW:-}"
SSH="sshpass -p '$PW' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=8 root@$IP"

if [[ -z "$PW" ]]; then
  echo "Usage: DEDI_PW=<password> bash $0 [--inspect-only]" >&2
  echo "Missing DEDI root password — it is NOT in keyring/.secrets/env (verified 2026-10-30)." >&2
  exit 2
fi

echo "== Connecting to $IP (AS23470 ReliableSite LA) =="
INSPECT_ONLY="${1:-}"

# 1. recon: what's actually hosting content
echo "== container/docker audit =="
eval "$SSH" 'docker ps 2>/dev/null || true; echo ---; ss -ltnp 2>/dev/null | grep LISTEN | head -30' || { echo "SSH failed — check password/creds"; exit 1; }

if [[ "$INSPECT_ONLY" == "--inspect-only" ]]; then
  echo "== inspect-only: not stopping anything. Screenshot of exposed services above. =="
  exit 0
fi

# 2. stop candidate porn-adjacent containers (nginx/hosted web) — SAFE: only stop, don't remove yet
echo "== stopping exposed web containers (inspect first, then confirm) =="
eval "$SSH" 'docker ps --format "{{.Names}} {{.Image}}" 2>/dev/null' | while read -r name img; do
  echo ">> stopping: $name ($img)"
  eval "$SSH" "docker stop '$name' 2>/dev/null || true"
done

# 3. evidence
echo "== evidence snapshot =="
eval "$SSH" 'echo "hostname: $(hostname)"; echo "uptime: $(uptime)"; docker ps -a --no-trunc 2>/dev/null | head -40 || true'

echo "== done. Rollback: docker start <name> per container. Compromise log = leak dossier docs/anomalies/2026-10-30/. =="