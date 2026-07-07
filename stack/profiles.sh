#!/usr/bin/env bash
# Process module lists per profile (one module = one stack/modules/<name>.yaml)

stack_profile_modules() {
  local profile="${1:-core}"
  case "$profile" in
    core)
      printf '%s\n' llama-herder openfang prometheus caddy
      ;;
    full)
      printf '%s\n' \
        llama-herder openfang prometheus caddy \
        landing watchdog hf-downloader yote rust-web
      ;;
    *)
      echo "unknown profile: $profile (core|full)" >&2
      return 1
      ;;
  esac
}