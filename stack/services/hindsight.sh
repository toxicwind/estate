#!/usr/bin/env bash
# Hindsight — vectorize-io/hindsight agent memory (sovereign)
# Maps: 8888 -> HINDSIGHT_API_PORT (25117), 9999 -> HINDSIGHT_CP_PORT (25118)
# Docs: https://hindsight.vectorize.io/developer/installation
# Image: ghcr.io/vectorize-io/hindsight:latest  (~9GB, named volume for embedded pg)
set -euo pipefail
SOV="${SOVEREIGN_ROOT:-/home/toxic/sovereign}"
source "$SOV/stack/lib-ports.sh"
require_env HINDSIGHT_API_PORT
require_env HINDSIGHT_CP_PORT

API_PORT="$HINDSIGHT_API_PORT"
CP_PORT="$HINDSIGHT_CP_PORT"

# Resolve LLM credentials — prefer Hindsight-specific, fallback to OpenAI
# 25+ providers supported via HINDSIGHT_API_LLM_PROVIDER (openai, anthropic, groq, ollama, etc.)
LLM_KEY="${HINDSIGHT_API_LLM_API_KEY:-${OPENAI_API_KEY:-}}"
LLM_PROVIDER="${HINDSIGHT_API_LLM_PROVIDER:-litellm}"
# HERD endpoint (port 25100) - beellama/exaone-4-0-1-2b-iq4xs
HINDSIGHT_API_LLM_API_URL="${HINDSIGHT_API_LLM_API_URL:-http://127.0.0.1:25100}"
# Optional model override (defaults inside image: gpt-5-mini or similar)
LLM_MODEL="${HINDSIGHT_API_LLM_MODEL:-beellama/exaone-4-0-1-2b-iq4xs}"

# Allow empty key for local providers (ollama, lmstudio) or Cloud-bypass;
# container still starts but retain/reflect requiring LLM will error until key is set.
if [[ -z "${LLM_KEY}" ]]; then
  echo "[hindsight] WARN: HINDSIGHT_API_LLM_API_KEY/OPENAI_API_KEY empty — LLM calls will fail until set." >&2
  echo "[hindsight]      Set in ~/.secrets or .env.local: export HINDSIGHT_API_LLM_API_KEY=sk-..." >&2
fi

# Clean stale listeners / containers (pitchfork will retry on failure)
fuser -k "${API_PORT}/tcp" 2>/dev/null || true
fuser -k "${CP_PORT}/tcp" 2>/dev/null || true
docker rm -f hindsight 2>/dev/null || true
sleep 0.3

# Ensure named volume exists (preferred over host bind; avoids UID 1000 chown issues)
docker volume create hindsight-data >/dev/null 2>&1 || true

# Build docker env passthrough
DOCKER_ENV=(
  -e "HINDSIGHT_API_LLM_PROVIDER=${LLM_PROVIDER}"
  -e "HINDSIGHT_API_LLM_API_KEY=llama-swap-local-key"
)
if [[ -n "${LLM_KEY}" ]]; then
  DOCKER_ENV+=(-e "HINDSIGHT_API_LLM_API_KEY=${LLM_KEY}")
fi
if [[ -n "${LLM_MODEL}" ]]; then
  DOCKER_ENV+=(-e "HINDSIGHT_API_LLM_MODEL=${LLM_MODEL}")
fi
# Pass through any HINDSIGHT_* overrides from host env (cp access key, etc.)
for v in HINDSIGHT_CP_ACCESS_KEY HINDSIGHT_CP_DATAPLANE_API_URL HINDSIGHT_API_PORT HINDSIGHT_CP_PORT; do
  if [[ -n "${!v:-}" ]]; then
    DOCKER_ENV+=(-e "$v=${!v}")
  fi
done

echo "[hindsight] starting ghcr.io/vectorize-io/hindsight:latest on :${API_PORT}->8888 api, :${CP_PORT}->9999 cp (provider=${LLM_PROVIDER})"

# exec replaces shell — pitchfork tracks docker as the daemon pid; logs stream via pitchfork.
# --pull always ensures latest; --rm lets pitchfork restart cleanly; --shm-size=1g required by docs.
# --name hindsight stable for volume attachment.
exec docker run --rm \
  --pull always \
  --name hindsight \
  --restart no \
  --shm-size=1g \
  -p "127.0.0.1:${API_PORT}:8888" \
  -p "127.0.0.1:${CP_PORT}:9999" \
  -v hindsight-data:/home/hindsight/.pg0 \
  "${DOCKER_ENV[@]}" \
  ghcr.io/vectorize-io/hindsight:latest
