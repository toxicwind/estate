#!/bin/bash
for i in $(seq 1 10); do
  RESP=$(curl -s --max-time 120 http://127.0.0.1:25104/v1/chat/completions -H 'Content-Type: application/json' -d '{"model":"sovereign/free","messages":[{"role":"user","content":"Reply with exactly: SOVEREIGN_ROUTER_OK and nothing else. No thinking, just output the string."}],"max_tokens":300}')
  echo "attempt $i @ $(date -u +%H:%M:%S): $(echo "$RESP" | head -c 220)"
  if echo "$RESP" | grep -q 'SOVEREIGN_ROUTER_OK'; then echo "PROBE_OK after $i attempts"; break; fi
  sleep 45
done
