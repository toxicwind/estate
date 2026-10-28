#!/usr/bin/env bash
# ccache proof via buildsrv (runs ON yote).
# Proves: buildsrv jobs inherit CCACHE_DIR from the daemon env, and a second
# compilation of identical inputs hits the ccache cache. Uses `ccache gcc`
# directly (ccache as a real executable launcher, not a CC="ccache gcc"
# shell string).
set -euo pipefail

PROOF_DIR="/home/toxic/buildsrv-proof/ccache-c"
BIN="/home/toxic/bin/buildsrv"

echo "=== 1. create test C program ==="
rm -rf "$PROOF_DIR"
mkdir -p "$PROOF_DIR"
cat > "$PROOF_DIR/main.c" <<'EOF'
#include <stdio.h>
#include <stdint.h>
uint64_t fib(uint64_t n) { return n < 2 ? n : fib(n-1) + fib(n-2); }
uint64_t psum(const uint64_t *v, int n) {
    uint64_t s = 0;
    for (int i = 0; i < n; i++) s += v[i];
    return s;
}
int main(void) {
    uint64_t v[64];
    for (int i = 0; i < 64; i++) v[i] = (uint64_t)(i * i + 1);
    printf("psum=%llu fib20=%llu\n",
           (unsigned long long)psum(v, 64),
           (unsigned long long)fib(20));
    return 0;
}
EOF

echo "=== 2. zero ccache stats ==="
ccache -z
ccache -s -v | grep -E "Hits:|Misses:|Cache size"

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

echo "=== 3. submit job 1 (cold compile via ccache launcher) ==="
t0=$(date +%s.%N)
out1="$($BIN submit --name ccache-proof-1 --env PROOF_ITER=1 --repo "$PROOF_DIR" \
    --toolchain python3 --cmd "ccache gcc -O2 -c main.c -o main.o && gcc -O2 -o hello main.o && ./hello")"
echo "$out1"
id1="$(echo "$out1" | awk '/^QUEUED/{print $2}')"
r1="$(wait_job "$id1")"
t1=$(date +%s.%N)
echo "job1 result: $r1  wall=$(wall $t0 $t1)s"
ccache -s -v | grep -E "Hits:|Misses:"

echo "=== 4. touch source + submit job 2 (busted artifact cache) ==="
touch "$PROOF_DIR/main.c"
t0=$(date +%s.%N)
out2="$($BIN submit --name ccache-proof-2 --env PROOF_ITER=2 --repo "$PROOF_DIR" \
    --toolchain python3 \
    --cmd "ccache gcc -O2 -c main.c -o main.o && gcc -O2 -o hello main.o && ./hello")"
echo "$out2"
id2="$(echo "$out2" | awk '/^QUEUED/{print $2}')"
r2="$(wait_job "$id2")"
t1=$(date +%s.%N)
echo "job2 result: $r2  wall=$(wall $t0 $t1)s"
ccache -s -v | grep -E "Hits:|Misses:"

if [ "$r2" = "CACHED" ]; then
    echo "PROOF INVALID: job 2 short-circuited on the artifact cache"
    exit 1
fi
echo "=== PROOF COMPLETE ==="
