#!/bin/bash
set -e

PROXY="http://127.0.0.1:25008"
MODEL="http://127.0.0.1:25001"

echo "=== NF-CoT Proxy Test Suite ==="
echo

# Test 1: Health check
echo "1. Health check..."
curl -s $PROXY/health | python3 -m json.tool
echo

# Test 2: Model list
echo "2. Model list..."
curl -s $PROXY/v1/models | python3 -m json.tool | head -20
echo

# Test 3: Simple completion (no think token)
echo "3. Simple completion (should work even without flow)..."
curl -s $PROXY/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Say hi in 3 words"}],
    "max_tokens": 20
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['choices'][0]['message']['content']); print('Receipt:', d.get('sovereign_receipt',{}).get('flow_enabled'))"
echo

# Test 4: Completion with think token (tests flow injection)
echo "4. Completion with <think> (tests latent injection)..."
curl -s $PROXY/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Think step by step: 2+2=? Use <think> tags"}],
    "max_tokens": 100,
    "temperature": 0.3
  }' | python3 -c "
import sys,json
d=json.load(sys.stdin)
content=d['choices'][0]['message']['content']
receipt=d.get('sovereign_receipt',{})
print('Response:', content[:200])
print('Flow enabled:', receipt.get('flow_enabled'))
print('Latent:', receipt.get('latent'))
print('Has injection:', '<|latent:' in content)
"
echo

# Test 5: Check flow file
echo "5. Flow file status..."
ls -lh nfcot_flow.pt 2>/dev/null || echo "No flow file"
python3 -c "
import torch,os
if os.path.exists('nfcot_flow.pt'):
    sd=torch.load('nfcot_flow.pt', map_location='cpu')
    dim=sd['layers.0.net.0.weight'].shape[1]*2
    print(f'Flow dim: {dim}')
    print(f'Layers: {len([k for k in sd.keys() if \"weight\" in k])}')
else:
    print('No flow file found')
"
echo

# Test 6: Simulate flow failure
echo "6. Testing fallback (rename flow, restart not needed)..."
mv nfcot_flow.pt nfcot_flow.pt.test 2>/dev/null || true
sleep 1
curl -s $PROXY/health | python3 -c "import sys,json; d=json.load(sys.stdin); print('Flow enabled after rename:', d['flow_enabled'])"
mv nfcot_flow.pt.test nfcot_flow.pt 2>/dev/null || true
echo

echo "=== Tests complete ==="
