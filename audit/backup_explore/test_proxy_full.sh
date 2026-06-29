#!/bin/bash
set -e

PROXY_PORT=25008
PROXY_PID=""
PROXY_LOG="/tmp/nfcot_proxy_test.log"

cleanup() {
    echo
    echo "Cleaning up..."
    if [! -z "$PROXY_PID" ] && kill -0 $PROXY_PID 2>/dev/null; then
        kill $PROXY_PID
        wait $PROXY_PID 2>/dev/null || true
        echo "Killed test proxy (PID $PROXY_PID)"
    fi
    # Kill any other proxies on the port
    pkill -f "uvicorn.*:$PROXY_PORT" 2>/dev/null || true
    pkill -f "nfcot.*proxy" 2>/dev/null || true
}

trap cleanup EXIT INT TERM

echo "=== NF-CoT Proxy Full Test ==="
echo

# 1. Kill existing proxies
echo "1. Killing existing proxies on port $PROXY_PORT..."
lsof -ti:$PROXY_PORT | xargs kill -9 2>/dev/null || true
pkill -f "uvicorn.*$PROXY_PORT" 2>/dev/null || true
sleep 1
echo "✓ Cleaned"

# 2. Check model is up
echo
echo "2. Checking upstream model..."
if! curl -s http://127.0.0.1:25001/v1/models > /dev/null; then
    echo "✗ Upstream model not running on port 25001"
    exit 1
fi
echo "✓ Model is up"

# 3. Start proxy
echo
echo "3. Starting proxy..."
rm -f $PROXY_LOG
nohup python3 nfcot_proxy.py > $PROXY_LOG 2>&1 &
PROXY_PID=$!
echo "Started proxy PID $PROXY_PID, logging to $PROXY_LOG"

# Wait for startup
echo -n "Waiting for proxy to start"
for i in {1..30}; do
    if curl -s http://127.0.0.1:$PROXY_PORT/health > /dev/null 2>&1; then
        echo " ✓"
        break
    fi
    echo -n "."
    sleep 1
done

if! curl -s http://127.0.0.1:$PROXY_PORT/health > /dev/null; then
    echo " ✗ Failed to start"
    tail -20 $PROXY_LOG
    exit 1
fi

# 4. Show startup info
echo
echo "4. Proxy status:"
curl -s http://127.0.0.1:$PROXY_PORT/health | python3 -m json.tool

# 5. Run tests
echo
echo "5. Running tests..."
echo

echo "--- Test A: Simple completion ---"
curl -s http://127.0.0.1:$PROXY_PORT/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hi"}],"max_tokens":10}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('Response:', d['choices'][0]['message']['content'].strip()); print('Flow:', d.get('sovereign_receipt',{}).get('flow_enabled'))"

echo
echo "--- Test B: Think token ---"
curl -s http://127.0.0.1:$PROXY_PORT/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Solve: 5*5. Think first."}],"max_tokens":50,"temperature":0.1}' \
  | python3 -c "
import sys,json
d=json.load(sys.stdin)
c=d['choices'][0]['message']['content']
r=d.get('sovereign_receipt',{})
print('Has <think>:', '<think>' in c or '<|thought|>' in c)
print('Has latent:', '<|latent:' in c)
print('Flow enabled:', r.get('flow_enabled'))
print('Latent value:', r.get('latent'))
"

echo
echo "--- Test C: Receipt ---"
curl -s http://127.0.0.1:$PROXY_PORT/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"test"}],"max_tokens":5}' \
  | python3 -m json.tool | grep -A6 sovereign_receipt

# 6. Show logs
echo
echo "6. Recent logs:"
tail -15 $PROXY_LOG | grep -E "INFO|WARNING|ERROR|RECEIPT|Loaded|fallback"

echo
echo "=== Test complete ==="
echo "Proxy still running on PID $PROXY_PID"
echo "Logs: tail -f $PROXY_LOG"
echo "To stop: kill $PROXY_PID"
