#!/usr/bin/env bash
# Process module lists per profile (one module = one stack/modules/<name>.yaml)

stack_profile_modules() {
  local profile="${1:-sovereign}"
  case "$profile" in
    core)
      # LLM ingress + mesh API + metrics + edge only
      printf '%s\n' llama-herder openfang prometheus
      ;;
    sovereign)
      # Daily driver — core + telegram bot + rust ranking dashboard
      printf '%s\n' \
        llama-herder openfang prometheus \
        yote rust-web
      ;;
    full)
      printf '%s\n' \
        llama-herder openfang prometheus \
        yote rust-web \
        landing watchdog hf-downloader
      ;;
    *)
      echo "unknown profile: $profile (core|sovereign|full)" >&2
      return 1
      ;;
  esac
}