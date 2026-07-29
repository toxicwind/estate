#!/bin/bash
set -e

echo "=== Starting remaining sovereign services ==="
cd /home/toxic/sovereign

# Start services in dependency order
echo "Starting llama-swap (dependency for many services)..."
mise run up-llama-swap
sleep 5

echo "Starting openfang..."
mise run up-openfang
sleep 3

echo "Starting sovereign-router..."
mise run up-sovereign-router
sleep 3

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

echo "=== Service status ==="
pitchfork list

echo "=== Port check (25xxx range) ==="
ss -tlnp | grep ':25' || echo "No 25xxx ports found"

echo "=== Health checks ==="
for service in "llama-swap:25100" "sovereign-router:25104" "byte-vision-proxy:25120" "prometheus:25105" "grafana:25110"; do
    IFS=':' read -r name port <<< "$service"
    status=$(curl -s "http://127.0.0.1:$port/health" || echo "unavailable")
    echo "$name ($port): $status"
done

echo "=== Done ==="
