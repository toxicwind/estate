#!/usr/bin/env bash
# byte-vision mock - placeholder for vision API
# Returns health check response
PORT="${BYTE_VISION_PORT:-25121}"
echo "byte-vision-mock listening on $PORT"
while true; do
  sleep 60
done
