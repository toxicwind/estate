#!/usr/bin/env bash
# Build the bffi-rustc bridge. Requires nightly + rustc-dev + llvm-tools.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
rustup component list --installed | grep -q rustc-dev || rustup component add rustc-dev
rustup component list --installed | grep -q llvm-tools || rustup component add llvm-tools
cargo build --release
echo "built: $(pwd)/target/release/libbffi_rustc_bridge.so"
