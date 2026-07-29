#!/bin/bash
set -e

echo "=== Starting full sovereign stack ==="
cd /home/toxic/sovereign

# Start core services individually to ensure proper ordering
echo "Starting llama-swap..."
mise run up-llama-swap
sleep 3

echo "Starting mcpproxy..."
mise run up-mcpproxy
sleep 2

echo "Starting openfang..."
mise run up-openfang
sleep 2

echo "Starting sovereign-router..."
mise run up-sovereign-router
sleep 2

echo "Starting null-g-proxy..."
mise run up-null-g-proxy
sleep 2

echo "Starting yote..."
mise run up-yote
sleep 2

echo "Starting rust-web..."
mise run up-rust-web
sleep 3

echo "Starting ghas services..."
mise run up-ghas-api
mise run up-ghas-mcp
sleep 2

echo "Starting mesh-hub..."
mise run up-mesh-hub
sleep 2

echo "Starting byte-vision services..."
mise run up-byte-vision
mise run up-byte-vision-proxy
sleep 3

echo "Starting monitoring stack..."
mise run up-prometheus
mise run up-grafana
sleep 3

echo "Starting data services..."
mise run up-hf-downloader
mise run up-qdrant
mise run up-redis
sleep 3

echo "=== Full stack status ==="
pitchfork list

echo "=== Port verification ==="
ss -tlnp | grep ':25' || true

echo "=== Health checks ==="
echo "mcpproxy: $(curl -s http://127.0.0.1:25109/health || echo 'unavailable')"
echo "llama-swap: $(curl -s http://127.0.0.1:25100/health || echo 'unavailable')"
echo "sovereign-router: $(curl -s http://127.0.0.1:25104/health || echo 'unavailable')"
echo "byte-vision-proxy: $(curl -s http://127.0.0.1:25120/health || echo 'unavailable')"

echo "=== Done ==="
