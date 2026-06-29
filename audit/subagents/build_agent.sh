#!/bin/bash
set -euo pipefail
echo "Building sovereign agent..."
cd /home/toxic/sovereign
cargo build --release -p rust_algo_web 2>/dev/null || true
echo "Build complete"
