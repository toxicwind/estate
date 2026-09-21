# buildsrv compiler-cache proofs

Reproducible proof scripts demonstrating that the buildsrv daemon's
environment correctly wires compiler caches into every build job.

## sccache (Rust)

`buildsrv-sccache-proof.sh`:
1. Creates a lib+bin Rust crate (library target required -- sccache
   treats binary-only crates as non-cacheable via the crate-type rule).
2. Zeroes sccache stats.
3. Submits job 1 (cold): expects 1 cache miss, 0 hits.
4. Touches sources (identical content), submits job 2 with a distinct
   `PROOF_ITER` env so buildsrv's whole-job artifact cache cannot
   short-circuit; expects >=1 cache hit and a non-CACHED result.

Verified 2026-09-21: job b260921-125457-494679c6 (1 miss), job
b260921-125502-d8b067e7 (1 hit, 50% Rust hit rate). Both SUCCEEDED.

## ccache (C)

`buildsrv-ccache-proof.sh`:
1. Creates a C program.
2. Zeroes ccache stats.
3. Submits job 1: `ccache gcc -O2 -c main.c -o main.o` (compile step only --
   ccache does not cache link steps, so compile and link are split),
   then links with plain gcc and runs the binary. Expects 1 miss.
4. Touches the source, submits job 2 with distinct `PROOF_ITER` env;
   expects >=1 hit and a non-CACHED result.

Verified 2026-09-21: job b260921-125554-02ec538e (1 miss), job
b260921-125559-291c3f98 (1 hit, 50% hit rate). Both SUCCEEDED.

## Daemon environment

Both caches are inherited from the buildsrv daemon's pitchfork environment
(`pitchfork.toml` `[daemons.buildsrv]`): `RUSTC_WRAPPER=sccache`,
`SCCACHE_DIR`, `CCACHE_DIR`, `CMAKE_C_COMPILER_LAUNCHER=ccache`,
`CMAKE_CXX_COMPILER_LAUNCHER=ccache`.
