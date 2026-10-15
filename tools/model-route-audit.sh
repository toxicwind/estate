#!/usr/bin/env bash
# model-route-audit.sh — find anything on this box that points agents at the
# LOCAL herd models (llama-swap on :25100, toolcall-local on :25152).
#
# User's order (2026-10-13): local herd models are NOT ready. Nobody uses
# them — not as primary, not as fallback, not as candidates. The working
# chain is: cuttinggate :25200 -> flock :25193 -> vans :20128, NIM-backed
# models through flock (e.g. openai/gpt-oss-20b).
#
# Usage: model-route-audit.sh
# Exit:  0 = no consumer hits. 1 = consumer hits found (fix them).
# Definition-side files (herd.yaml, herd.d/, llama-swap config, pitchfork
# stanzas for the local services themselves, the port registry) are
# informational only — the local services existing is not consumption.
# Session transcripts, caches, logs and databases are history, not config,
# and are excluded. NOTE: estate/config/tau/ is the mirror of ~/.tau —
# fix the source in ~/.tau, never the mirror.

PATTERNS='127\.0\.0\.1:25100|localhost:25100|:25100|local-fast|local-quality|local-longctx|127\.0\.0\.1:25152|:25152'

SURFACES=(
  /home/toxic/.secrets
  /home/toxic/.env
  /home/toxic/.config/environment.d
  /home/toxic/.tau/agent
  /home/toxic/.tau/config.yml
  /home/toxic/.tau/model-router.json
  /home/toxic/.tau/profiles
  /home/toxic/.flock-data/config.json
  /home/toxic/estate/config
  /home/toxic/estate/stack
  /home/toxic/estate/pitchfork.toml
)

EXCLUDES=(
  --exclude='*.bak*' --exclude='*bak*' --exclude='*.log' --exclude='*.db' --exclude='*.db-*'
  --exclude='model-route-audit.sh'
  --exclude-dir=node_modules --exclude-dir=.git
  --exclude-dir=sessions --exclude-dir=cache --exclude-dir=blobs
  --exclude-dir=memories --exclude-dir=logs
)

hits_file="$(mktemp)"
defs_file="$(mktemp)"
trap 'rm -f "$hits_file" "$defs_file"' EXIT

for surface in "${SURFACES[@]}"; do
  [ -e "$surface" ] || continue
  grep -rnE "$PATTERNS" "$surface" "${EXCLUDES[@]}" 2>/dev/null \
  | cut -c1-160 \
  | while IFS= read -r line; do
      case "$line" in
        *"/herd.yaml:"*|*"/herd.d/"*|*"pitchfork.toml:"*|*"llama-swap"*|*"ports.env:"*|*"model_constraints.yaml:"*)
          echo "$line" >> "$defs_file" ;;
        *) echo "$line" >> "$hits_file" ;;
      esac
    done
done

echo "== model-route-audit =="
echo "-- hits per file:"
if [ -s "$hits_file" ]; then
  sed 's/:[0-9]*:.*//' "$hits_file" | sort | uniq -c | sort -rn
  hit_count=$(wc -l < "$hits_file")
else
  echo "(none)"
  hit_count=0
fi
echo "-- sample hits (first 25, lines capped at 160 chars):"
if [ -s "$hits_file" ]; then head -25 "$hits_file"; else echo "(none)"; fi
echo "-- herd-internal definitions (informational): $(wc -l < "$defs_file") lines"
echo "consumer hits: $hit_count"
[ "$hit_count" -eq 0 ]
