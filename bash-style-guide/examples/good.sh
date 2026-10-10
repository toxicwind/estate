#!/usr/bin/env bash
# ---
# example: demonstrate the estate conventions on a small script.
# ---

set -o errexit
set -o nounset
set -o pipefail
set -o errtrace
shopt -s inherit_errexit
shopt -s shift_verbose

# --- 01 - constants ---
readonly MAX_RETRIES=3
readonly BACKOFF_SECONDS=2

# --- 02 - helpers ---
_log() {
  local level="$1"
  shift
  printf "[%s] %s\n" "$level" "$*" >&2
}

_retry() {
  local attempt=0
  local delay="$BACKOFF_SECONDS"
  until "$@"; do
    attempt=$((attempt + 1))
    if (( attempt >= MAX_RETRIES )); then
      _log error "giving up after $attempt attempts"
      return 1
    fi
    _log warn "attempt $attempt failed, retrying in ${delay}s"
    sleep "$delay"
    delay=$((delay * 2))
  done
}

# --- 03 - main ---
main() {
  local target="${1:-https://example.com}"
  _log info "fetching $target"
  _retry curl --silent --fail --max-time 10 "$target"
  _log info "done"
}

main "$@"
