#!/usr/bin/env bash
set -exuo pipefail
# MESH_SEPT_2026_FIX_EXPERIMENTAL - maximal unblinded - pulled from raw.githubusercontent.com sources
cd ~/projects/sovereign-projects/tau
pwd
git status --porcelain | head -n 100
git diff --stat | head -n 100
env | grep -E "RUST|CARGO|BUN|NAPI|OMP" | sort || true
rustup show || true
rustc --version; cargo --version; bun --version
ss -tlnp | grep 9090 || true
ps aux | grep -E "collab|omp" | grep -v grep || true
cat ~/.tau/agent/mcp.json 2>/dev/null | head -n 100 || echo no mcp.json
ls -l ~/.tau/agent/extensions/ 2>/dev/null | head -n 100
ls -l /tmp/agent-trigger.txt 2>/dev/null || echo missing trigger
which qemu-img || echo missing qemu-img

# raw.githubusercontent.com maximal configs:
# obsidian-vault-mind: <vault>/.vault-mind/ + vault-mind.env + PVM_API_TOKEN + 127.0.0.1:11435
# pi-model-discovery: ~/.pi/agent/local-providers.json with debug, syncOnStartup, addToScope, providers.ollama.enabled, baseUrl, cleanupStale, cacheTtlHours
# pi-model-router: ~/.pi/agent/model-router.json with defaultProfile, classifierModel, maxSessionBudget, largeContextThreshold, phaseBias, rules, profiles, features.rateLimitFallback, fallbackSequence

cat > rust-toolchain.toml <<'TOML'
[toolchain]
channel = "nightly"
components = ["rustfmt","clippy","rust-src","rust-analyzer","llvm-tools"]
profile = "complete"
targets = ["x86_64-unknown-linux-gnu","wasm32-wasip1"]
TOML

rustup toolchain install nightly --profile complete -c rustfmt,clippy,rust-src,rust-analyzer,llvm-tools
rustup default nightly
rustup override set nightly --path $(pwd)
rustup update

cargo clean
rm -rf target/ crates/pi-natives/target crates/pi-natives/index.node
rm -rf node_modules/.cache.turbo dist packages/*/dist packages/natives/*.node

cargo +nightly update --aggressive
cargo +nightly tree -p pi-natives 2>&1 | head -n 100
HUSKY=0 bun install --force
bun update || true
bun add -d @napi-rs/cli@latest @napi-rs/wasm-runtime@latest || true
HUSKY=0 bun install

touch /tmp/agent-trigger.txt
chmod 666 /tmp/agent-trigger.txt
sudo apt-get update && sudo apt-get install -y qemu-utils || true

RUST_BACKTRACE=1 RUSTUP_TOOLCHAIN=nightly bun --cwd packages/natives run build --verbose 2>&1 | tee /tmp/natives.log
RUSTUP_TOOLCHAIN=nightly bun --cwd packages/natives run gen:native
ls -l packages/natives/src/*.ts | head

RUSTUP_TOOLCHAIN=nightly bun --cwd packages/collab-web run gen:tool-views --verbose
RUSTUP_TOOLCHAIN=nightly bun --cwd packages/stats run gen:stats --verbose
cat packages/ai/src/providers/data/groq.models.ts | head -n 40

RUSTUP_TOOLCHAIN=nightly bun --cwd packages/coding-agent run build --verbose 2>&1 | tee /tmp/coding-agent.log
ls -lh packages/coding-agent/dist/
cp packages/coding-agent/dist/tau ~/.local/bin/tau 2>/dev/null || cp packages/coding-agent/dist/tau-* ~/.local/bin/tau 2>/dev/null || true
~/.local/bin/tau --version || true

ln -sfn ~/projects/pi-vault-mind packages/pi-vault-mind
cat ~/projects/pi-vault-mind/src/extension-packages.ts
cat ~/projects/pi-vault-mind/src/config-keys.ts
node ~/projects/pi-vault-mind/scripts/generate-extension-packages-json.mjs --verbose || true
node ~/projects/pi-vault-mind/scripts/generate-config-keys-json.mjs --verbose || true
cat ~/projects/pi-vault-mind/config-keys.json 2>/dev/null | head -n 100
cat ~/projects/pi-vault-mind/extension-packages.json 2>/dev/null | head -n 100
RUSTUP_TOOLCHAIN=nightly bun --cwd packages/pi-vault-mind run build --verbose 2>&1 | tail -n 30

RUSTUP_TOOLCHAIN=nightly HUSKY=0 bun run build --verbose 2>&1 | tee /tmp/tau.log | tail -n 100

pkill -f collab || true
sleep 2
RUSTUP_TOOLCHAIN=nightly bun --cwd packages/collab run dev --host 0.0.0.0 --port 9090 --verbose &
sleep 5
ss -tlnp | grep 9090 || true
curl -sk https://awrawr-pc:9090/ | head -n 20 || true
~/.local/bin/tau --version || true
echo MESH_SEPT_2026_FIX_EXPERIMENTAL DONE UNBLINDED
echo logs: /tmp/natives.log /tmp/coding-agent.log /tmp/tau.log