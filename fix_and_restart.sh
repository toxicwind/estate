#!/bin/bash
set -e

echo "=== Stopping all services ==="
cd /home/toxic/sovereign
mise run down 2>/dev/null || true
pkill -f pitchfork 2>/dev/null || true
sleep 2

echo "=== Starting services with fixed configuration ==="
source config/ports.env
export $(cut -d= -f1 config/ports.env)

# Start core services
mise run up

echo "=== Waiting for services to stabilize ==="
sleep 5

echo "=== Service status ==="
pitchfork list

echo "=== Port check ==="
ss -tlnp | grep ':25' || true

echo "=== Done ==="
