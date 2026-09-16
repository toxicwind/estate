#!/usr/bin/env bash
# Brain runtime generator - auto-detects current environment
# Usage: bash /home/toxic/brain/generate.sh

cd /home/toxic

# Detect environment
HOSTNAME=$(hostname)
CPU=$(lscpu | grep "Model name" | sed 's/.*: *//' | head -1)
RAM=$(free -h | awk '/Mem:/{print $2}')
GPU=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo "no gpu")

# Detect model
MODEL="${PI_MODEL:-longcat-2.0-free}"
PROVIDER="${PI_PROVIDER:-opencode}"

# Detect tools
TOOLS="[\"read\",\"write\",\"edit\",\"bash\",\"ls\",\"retrieve_tools\",\"describe_tool\",\"call_tool_destructive\"]"

# Generate runtime.json
cat > brain/runtime.json << EOF
{
  "generated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "host": {
    "hostname": "$HOSTNAME",
    "cpu": "$CPU",
    "ram": "$RAM",
    "gpu": "$GPU"
  },
  "model": {
    "name": "$MODEL",
    "provider": "$PROVIDER",
    "context_window": ${PI_MODEL_CONTEXT_WINDOW:-1000000}
  },
  "tools": {
    "native": $TOOLS,
    "count": 8
  },
  "env_vars": {
    "PI_DEBUG_STREAM": "${PI_DEBUG_STREAM:-1}",
    "PI_DEBUG": "${PI_DEBUG:-1}",
    "PI_MODEL_CONTEXT_WINDOW": "${PI_MODEL_CONTEXT_WINDOW:-1000000}",
    "PI_BRAIN_HASH": "$(sha256sum brain/identity.json | awk '{print $1}')"
  }
}
EOF

echo "Generated brain/runtime.json"
cat brain/runtime.json
