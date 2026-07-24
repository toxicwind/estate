#!/bin/bash
# Wrapper to start pitchfork supervisor and capture output safely
cd /home/toxic/sovereign
echo "=== Starting pitchfork supervisor ==="
pitchfork supervisor start > /tmp/pitchfork_sup.log 2>&1
echo "EXIT=$?"
echo "=== Supervisor output ==="
cat /tmp/pitchfork_sup.log
echo "=== Done ==="
