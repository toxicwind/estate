#!/bin/bash
cd /home/toxic/sovereign
echo "=== MISE E2E TEST ==="
echo "Date: $(date)"

echo ""
echo "=== 1. TOOL CHECKS ==="
echo -n "mise: "; mise --version 2>&1 | head -1
echo -n "bun: "; bun --version 2>&1
echo -n "node: "; node --version 2>&1
echo -n "python3: "; python3 --version 2>&1
echo -n "rustc: "; rustc --version 2>&1
echo -n "go: "; go version 2>&1 | awk '{print $3}'
echo -n "pitchfork: "; /home/toxic/.local/bin/pitchfork --version 2>/dev/null
echo -n "redis-server: "; redis-server --version 2>&1 | awk '{print $3}'
echo -n "qdrant: "; /home/toxic/.cargo/bin/qdrant --version 2>&1 | head -1
echo -n "mcpproxy: "; /usr/local/bin/mcpproxy --version 2>&1

echo ""
echo "=== 2. ENV CHECKS ==="
echo -n "SOVEREIGN_ROOT: "; echo ${SOVEREIGN_ROOT:-"(unset)"}
source config/ports.env 2>/dev/null
echo "LLAMA_SWAP_PORT=$LLAMA_SWAP_PORT"
echo "MCPPROXY_PORT=$MCPPROXY_PORT"
echo "SOVEREIGN_ROUTER_PORT=$SOVEREIGN_ROUTER_PORT"
echo "PROMETHEUS_PORT=$PROMETHEUS_PORT"
echo "GRAFANA_PORT=$GRAFANA_PORT"

echo ""
echo "=== 3. PORT CHECK ==="
for port in 25100 25101 25102 25103 25104 25105 25106 25107 25109 25110 25112 25113 25115 25120 25121 25122 6333 25199; do
  if ss -tlnp 2>/dev/null | grep -q ":${port} "; then
    echo "  :${port} LISTENING"
  else
    echo "  :${port} closed"
  fi
done

echo ""
echo "=== 4. HEALTH CHECKS ==="
for svc in "llama-swap:25100:/health" "mcpproxy:25109:/health" "sovereign-router:25104:/health" "qdrant:6333:/" "prometheus:25105/-/healthy" "grafana:25110/api/health" "byte-vision:25121/health"; do
  IFS=: read name port path <<< "$svc"
  result=$(curl -sf -m 2 "http://127.0.0.1:${port}${path}" 2>&1)
  rc=$?
  if [ $rc -eq 0 ]; then
    echo "  $name (:${port}) -> OK"
  else
    echo "  $name (:${port}) -> DOWN (rc=$rc)"
  fi
done

echo ""
echo "=== 5. DOCKER ==="
ls -la /var/run/docker.sock 2>&1
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>&1 | head -10

echo ""
echo "=== 6. GIT STATUS ==="
git status --short 2>&1 | head -20
echo "Branch: $(git branch --show-current 2>&1)"
echo "Last commit: $(git log --oneline -1 2>&1)"

echo ""
echo "=== DONE ==="
