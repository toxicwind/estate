#!/usr/bin/env bash
# Deprecated: single mise run up starts all owned modules.
# Kept so old scripts sourcing this do not explode.
stack_profile_modules() {
  printf '%s\n' \
    llama-swap openfang ast-matrix null-g-proxy yote rust-web hf-downloader ghas-api
}
