#!/usr/bin/env bash
# Process module lists per profile (one module = one stack/modules/<name>.yaml)
# Owned-code services use bun --hot / cargo watch where applicable.
# prometheus/grafana/caddy = infra (no source hot-reload required).

stack_profile_modules() {
  local profile="${1:-sovereign}"
  case "$profile" in
    core)
      # Inference ingress + agent kernel + AST matrix (Zed router)
      printf '%s\n' \
        llama-swap \
        openfang \
        ast-matrix
      ;;
    sovereign)
      # Daily driver — owned hot-reload services
      printf '%s\n' \
        llama-swap \
        openfang \
        ast-matrix \
        null-g-proxy \
        yote \
        rust-web
      ;;
    full)
      # Daily + HF + optional edge + metrics
      printf '%s\n' \
        llama-swap \
        openfang \
        ast-matrix \
        null-g-proxy \
        yote \
        rust-web \
        hf-downloader \
        ghas-api \
        prometheus
      ;;
    infra)
      # Metrics/edge only (no owned app code)
      printf '%s\n' prometheus grafana caddy
      ;;
    *)
      echo "unknown profile: $profile (core|sovereign|full|infra)" >&2
      return 1
      ;;
  esac
}
