#!/bin/bash
cd /home/toxic/sovereign
echo "=== MISE E2E ==="
echo -n "mise: "; mise --version 2>&1 | head -1
echo -n "bun: "; bun --version 2>&1
echo -n "node: "; node --version 2>&1
echo -n "python3: "; python3 --version 2>&1
echo -n "rustc: "; rustc --version 2>&1
echo -n "go: "; go version 2>&1
echo -n "pitchfork: "; /home/toxic/.local/bin/pitchfork --version 2>/dev/null
echo -n "redis: "; redis-server --version 2>&1
echo -n "qdrant: "; /home/toxic/.cargo/bin/qdrant --version 2>&1 | head -1
echo -n "mcpproxy: "; /usr/local/bin/mcpproxy --version 2>&1
echo "=== TOOLS OK ==="
