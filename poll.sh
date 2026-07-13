#!/bin/bash
URL="http://127.0.0.1:25100/v1/models"
while true; do
  if curl -sf "$URL" > /dev/null; then
    echo "✅ llama-swap is up"
    sleep 10
  else
    echo "❌ llama-swap down – restarting..."
    pkill -9 -f llama-swap
    # restart your llama-server or llama-swap here
    # e.g.: llama-server -m ... &
    sleep 5
  fi
done