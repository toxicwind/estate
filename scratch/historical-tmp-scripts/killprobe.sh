#!/bin/bash
pkill -f "mesh/browserless/dist/index" 2>/dev/null
sleep 1
pgrep -af "mesh/browserless/dist" || echo CLEAN
