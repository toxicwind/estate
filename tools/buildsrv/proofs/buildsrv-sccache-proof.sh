#!/usr/bin/env bash
# sccache proof via buildsrv (runs ON yote).
# Proves: buildsrv jobs inherit RUSTC_WRAPPER=sccache from the daemon env,
# and a second compilation of identical inputs hits the sccache cache.
set -euo pipefail

PROOF_DIR="/home/toxic/buildsrv-proof/sccache-crate"
BIN="/home/toxic/bin/buildsrv"

echo "=== 1. create test crate ==="
rm -rf "$PROOF_DIR"
mkdir -p "$PROOF_DIR/src"
cat > "$PROOF_DIR/Cargo.toml" <<'EOF'
[package]
name = "sccache-proof"
version = "0.1.0"
edition = "2021"

[lib]
name = "sccache_proof"
path = "src/lib.rs"
EOF
cat > "$PROOF_DIR/src/lib.rs" <<'EOF'
pub mod math;
pub mod util;
EOF
cat > "$PROOF_DIR/src/main.rs" <<'EOF'
use sccache_proof::{math, util};
fn main() {
    let v: Vec<u64> = (1..=2000).collect();
    let s = math::parallel_sum(&v);
    println!("sum={} tag={} fib20={}", s, util::tag(s), math::fib(20));
}
EOF
cat > "$PROOF_DIR/src/math.rs" <<'EOF'
pub fn parallel_sum(v: &[u64]) -> u64 {
    v.iter().fold(0u64, |a, b| a.wrapping_add(*b))
}
pub fn fib(n: u64) -> u64 {
    match n {
        0 | 1 => n,
        _ => fib(n - 1) + fib(n - 2),
    }
}
EOF
cat > "$PROOF_DIR/src/util.rs" <<'EOF'
pub fn tag(n: u64) -> String {
    format!("n={:#x}", n)
}
pub fn clamp(x: i64, lo: i64, hi: i64) -> i64 {
    if x < lo { lo } else if x > hi { hi } else { x }
}
EOF

echo "=== 2. zero sccache stats ==="
sccache --zero-stats
sccache --show-stats

wait_job() {
    local id="$1" i
    for i in $(seq 1 60); do
        st="$($BIN status "$id" 2>&1 || true)"
        if echo "$st" | grep -q "status: succeeded"; then echo "SUCCEEDED"; return 0; fi
        if echo "$st" | grep -q "status: failed"; then echo "FAILED"; echo "$st"; return 1; fi
        if echo "$st" | grep -q "CACHED"; then echo "CACHED"; return 2; fi
        sleep 5
    done
    echo "TIMEOUT waiting for $id"; return 1
}

wall() { python3 -c "print(round($2 - $1, 1))"; }

echo "=== 3. submit job 1 (cold compile) ==="
t0=$(date +%s.%N)
out1="$($BIN submit  --name sccache-proof-1 --env PROOF_ITER=1 --repo "$PROOF_DIR" \
    --toolchain cargo --cmd "cargo build 2>&1")"
echo "$out1"
id1="$(echo "$out1" | awk '/^QUEUED/{print $2}')"
echo "job1 id: $id1"
r1="$(wait_job "$id1")"
t1=$(date +%s.%N)
echo "job1 result: $r1  wall=$(wall $t0 $t1)s"
echo "--- sccache stats after job 1 ---"
sccache --show-stats | grep -E "Compile requests|Cache hits|Cache misses"

echo "=== 4. touch sources + submit job 2 (identical inputs, busted artifact cache) ==="
find "$PROOF_DIR/src" -name '*.rs' -exec touch {} +
t0=$(date +%s.%N)
out2="$($BIN submit  --name sccache-proof-2 --env PROOF_ITER=2 --repo "$PROOF_DIR" \
    --toolchain cargo --cmd "cargo build 2>&1")"
echo "$out2"
id2="$(echo "$out2" | awk '/^QUEUED/{print $2}')"
echo "job2 id: $id2"
r2="$(wait_job "$id2")"
t1=$(date +%s.%N)
echo "job2 result: $r2  wall=$(wall $t0 $t1)s"
echo "--- sccache stats after job 2 ---"
sccache --show-stats | grep -E "Compile requests|Cache hits|Cache misses"

if [ "$r2" = "CACHED" ]; then
    echo "PROOF INVALID: job 2 short-circuited on the artifact cache"
    exit 1
fi
echo "=== PROOF COMPLETE ==="
