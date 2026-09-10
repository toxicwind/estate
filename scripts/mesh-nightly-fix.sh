#!/usr/bin/env bash
# MESH_SEPT_2026_FIX — permanent nightly build for tau + pi-natives + coding-agent
# Run: sudo -u toxic bash ~/sovereign/scripts/mesh-nightly-fix.sh
set -euo pipefail
export RUSTUP_TOOLCHAIN=nightly
export HUSKY=0
export RUST_BACKTRACE=1

TAU=~/projects/sovereign-projects/tau
cd "$TAU"
echo "=== [0/8] SNAPSHOT ==="
pwd
git status --short | head -n 60 || true
git diff --stat | head -n 60 || true
rustc --version || true
cargo --version || true
bun --version || true

echo "=== [1/8] SYSTEM NIGHTLY ==="
source ~/.cargo/env 2>/dev/null || true
rustup toolchain install nightly --profile complete \
  -c rustfmt,clippy,rust-src,rust-analyzer,llvm-tools
rustup toolchain install stable 2>/dev/null || true
rustup default nightly
rustup update
rustc --version
cargo --version
bun upgrade || true
bun --version

echo "=== [2/8] REPO PIN ==="
cat > rust-toolchain.toml <<'TOML'
[toolchain]
channel = "nightly"
components = ["rustfmt", "clippy", "rust-src", "rust-analyzer", "llvm-tools"]
profile = "complete"
targets = ["x86_64-unknown-linux-gnu", "wasm32-wasip1"]
TOML
rustup override set nightly --path "$(pwd)"
rustup show active-toolchain

echo "=== [3/8] RUST DEPS ==="
cargo clean
rm -rf target/ crates/pi-natives/target crates/pi-natives/index.node
rm -rf node_modules/.cache.turbo dist packages/*/dist packages/natives/*.node
cargo update --aggressive
cargo tree -p pi-natives 2>&1 | head -n 80 || true
cargo build -p pi-natives --verbose 2>&1 | tee /tmp/natives-cargo.log | tail -n 60
grep -n "alloc_error_hook" crates/pi-natives/src/lib.rs || echo "feature line not present"

echo "=== [4/8] JS/BUN DEPS ==="
rm -rf node_modules/.cache
bun install --force
bun update || true
bun add -d @napi-rs/cli@latest @napi-rs/wasm-runtime@latest || true
bun install

echo "=== [5/8] BUILD NATIVES ==="
bun --cwd packages/natives run build 2>&1 | tee /tmp/natives-nightly.log | tail -n 80
bun --cwd packages/natives run gen:native
ls -lh packages/natives/src/*.ts 2>/dev/null | head || true
ls -lh packages/natives/*.node 2>/dev/null || echo "no .node file"

echo "=== [6/8] BUILD CODING-AGENT ==="
bun --cwd packages/collab-web run gen:tool-views || true
bun --cwd packages/stats run gen:stats || true

# groq models guard
if [ ! -s packages/ai/src/providers/data/groq.models.ts ]; then
  echo "WARN: groq.models.ts empty, restoring from upstream"
  git checkout upstream/main -- packages/ai/src/providers/data/groq.models.ts 2>/dev/null || \
  git checkout origin/main -- packages/ai/src/providers/data/groq.models.ts 2>/dev/null || \
  echo "WARN: could not restore groq.models.ts"
fi
head -n 30 packages/ai/src/providers/data/groq.models.ts

bun --cwd packages/coding-agent run build 2>&1 | tee /tmp/coding-agent-nightly.log | tail -n 80
ls -lh packages/coding-agent/dist/ 2>/dev/null || echo "no dist"

# install binary
if [ -f packages/coding-agent/dist/omp ]; then
  cp packages/coding-agent/dist/omp ~/.local/bin/omp
  echo "installed omp binary"
elif ls packages/coding-agent/dist/omp-* 2>/dev/null; then
  cp packages/coding-agent/dist/omp-* ~/.local/bin/omp
  echo "installed omp binary (glob)"
fi
~/.local/bin/omp --version 2>/dev/null || true

echo "=== [7/8] VAULT-MIND + FULL MONOREPO ==="
ln -sfn ~/projects/pi-vault-mind packages/pi-vault-mind
bun install
bun --cwd packages/pi-vault-mind run build 2>&1 | tail -n 30 || true
bun run build 2>&1 | tee /tmp/tau-full-nightly.log | tail -n 80

echo "=== [8/8] START COLLAB 9090 ==="
pkill -f "collab run dev" || true
sleep 2
bun --cwd packages/collab run dev --host 0.0.0.0 --port 9090 &
COLLAB_PID=$!
echo "collab started pid=$COLLAB_PID"
sleep 5
ss -tlnp | grep 9090 || echo "port 9090 not up yet"
curl -sk https://awrawr-pc:9090/ 2>&1 | head -n 10 || true

echo "==========================================="
echo "MESH_SEPT_2026_FIX DONE"
echo "Logs:"
echo "  /tmp/natives-cargo.log"
echo "  /tmp/natives-nightly.log"
echo "  /tmp/coding-agent-nightly.log"
echo "  /tmp/tau-full-nightly.log"
echo "==========================================="
