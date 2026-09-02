#!/usr/bin/env bash
# Tester for sovereign freeproxy — global cache home/toxic
# Uses herd (llama-swap) on :25100 with freeproxy (pollinations, ovh, openrouter, cf-gw)
set -euo pipefail
HERD="${HERD:-http://127.0.0.1:25100}"
CACHE_DIR="${CACHE_DIR:-/home/toxic/cache/freeproxy}"
GOCACHE="${GOCACHE:-$(go env GOCACHE 2>/dev/null || echo /home/toxic/cache/go-build)}"

echo "=== sovereign freeproxy tester ==="
echo "HERD: $HERD"
echo "build cache: $GOCACHE (global home/toxic)"
echo "freeproxy cache: $CACHE_DIR"
echo "GOCACHE env: $(go env GOCACHE 2>/dev/null || echo 'n/a')"
echo ""

test_model() {
  local model="$1"
  echo "--- test $model ---"
  curl -s --max-time 15 "$HERD/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"$model\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],\"max_tokens\":10}" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('choices',[{}])[0].get('message',{}).get('content','')[:200] if 'choices' in d else str(d)[:500])" 2>&1 | head -20
  echo "HTTP:$?"
  echo ""
}

# Global cache check
echo "cache dir: $(ls -ld "$CACHE_DIR" 2>&1 | head -1)"
echo ""

# Test freeproxy models (via herd)
test_model "openai/gpt-oss-20b"  # pollinations-free via freeproxy
# test_model "Meta-Llama-3_3-70B-Instruct" # ovh (if enabled)
# test_model "google/gemma-3-27b-it:free" # openrouter free

echo "=== direct pollinations (bypass) ==="
curl -s --max-time 10 https://gen.pollinations.ai/v1/models 2>&1 | python3 -c "import sys,json; d=json.load(sys.stdin); print([m['id'] for m in d['data']][:5])" 2>&1 | head -20
echo ""
echo "tester done — build cache is global home/toxic: $GOCACHE"
