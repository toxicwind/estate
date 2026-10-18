#!/usr/bin/env bash
# smithers-gateway — Estate stack (pitchfork-managed)
# Permanent home for the estate Smithers Gateway singleton (:7331).
#
# Secret doctrine (2026-10-18): keys come from the secretsmith keyring
# FIRST (freedesktop Secret Service); ~/.secrets is the fallback, never
# the source of truth. Secrets travel in child-process env only — this
# script never prints, logs, or writes key material.
#
# The gateway's env is what every smithers-spawned agent inherits, so the
# model/routing keys (FLOCK_API_KEY, NIM_PROXY_API_KEY, ANTHROPIC_API_KEY,
# NVIDIA_API_KEY) must be present HERE, at gateway boot — not in whatever
# interactive shell happened to launch a run.
set -euo pipefail
SOV="${ESTATE_ROOT:-/home/toxic/estate}"
SMITH="${SOV}/ranch/secretsmith/bin/secretsmith"

# 1) fallback layer: the ~/.secrets vault record (silent).
set +a
# shellcheck disable=SC1091
[ -f "${HOME}/.secrets" ] && source "${HOME}/.secrets"
set -a

# 2) keyring layer: secretsmith exec injects keyring-resolved vars on top
#    (keyring wins; entries that don't exist in the keyring are skipped so
#    the fallback layer stands). Var=attrspec specs follow secretsmith env.
ENVS=()
spec_of() { # VAR  keyring-attr-pairs  -> append only if the item exists
  if "$SMITH" exec --env "__probe=${2}" -- true >/dev/null 2>&1; then
    ENVS+=(--env "${1}=${2}")
  fi
}
spec_of FLOCK_API_KEY      "service=flock"
spec_of NIM_PROXY_API_KEY  "service=nim,provider=nvidia"
spec_of NVIDIA_API_KEY     "service=nim,provider=nvidia"
spec_of ANTHROPIC_API_KEY  "service=anthropic"
spec_of OPENROUTER_API_KEY "service=openrouter"

cd "$SOV"
exec "$SMITH" exec "${ENVS[@]}" -- bunx smthrs gateway --idle-timeout 0
