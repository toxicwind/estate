# TAU NATIVES — differential correctness audit + hardening

## Objective
Prove the tau native addon (`pi_natives`) is CORRECT, not just fast. Build a
differential test harness comparing every native export against its reference
implementation, fix all discrepancies found, harden the loader fallback chain,
resolve the known grep perf regression, and get the nightly bench fully green.

## Background (verified 2026-09-17, awrawr-pc)
- Addon binaries: `packages/natives/native/pi_natives.linux-x64-modern.node`
  and `pi_natives.linux-x64-baseline.node` (~180MB each, built Sep 17 02:16).
- Loader: `packages/natives/native/loader-state.js` — `loadNative()`,
  `selectCpuVariant`, `resolveLoaderCandidates`, `getAddonFilenames`;
  fallback chain modern -> baseline -> default -> Node shim.
- Smoke test 2026-09-17 (9 checks, 8 pass, 1 parser artifact):
  `countTokens` deterministic, sane (201 tokens on fixture), empty->0,
  unicode-safe (17 tokens on multibyte fixture). Native `grep()` returns the
  SAME 4 matches as `rg --json` on a fixture tree — note the shape differs
  (`{path,lineNumber,line}` vs rg JSON); normalize key names in the harness.
- Known issues:
  1. `natives-grep` "Cargo registry content" case: native 2.0x SLOWER than rg
     (164.39ms vs 83.51ms) — the one perf regression in the nightly bench.
  2. `coding-agent-guard` bench fails: "No baseline found" (needs
     `bun scripts/bench-guard.ts --update` on this machine).
  3. `bench-title-models.ts` is orphaned — a SEPARATE lane is wiring it.
     Do not touch it.

## Work items

### 1. Differential correctness harness (the core deliverable)
Create `packages/natives/test/differential/` (bun test). For EVERY native
export that has a reference implementation, assert OUTPUT EQUALITY (not
timing) across an edge-case matrix:
- `grep` vs `rg --json` (normalize shapes first)
- `countTokens` vs `gpt-tokenizer` package
- `diffLines` vs `diff` npm package
- `extractSegments` / `highlightCode` vs their JS fallbacks where they exist
- any other export with a meaningful reference — enumerate them from
  `native/index.d.ts` and justify each skip in a comment

Edge-case matrix (every applicable function): unicode/multibyte, binary
files, empty inputs, 100MB+ inputs, CRLF line endings, overlapping regex
matches, symlinks, unreadable files, invalid UTF-8, deeply nested paths.
Determinism: same input twice -> byte-identical output.

### 2. Fix every discrepancy
Patch FORWARD. Fix in the Rust/napi source or the JS adapter — never revert,
never delete the native implementation to "fix" a mismatch. Rebuild the
addon (`bun --cwd=packages/natives run build` or the repo's documented
build), re-run the harness green. Record each fix as its own commit with the
failing differential case in the message.

### 3. Loader fallback-chain proof
Prove modern -> baseline -> default -> shim actually works:
- Temporarily rename the modern binary away, assert baseline loads and
  `grep`/`countTokens` still return correct results. Then baseline too,
  assert the shim/default path.
- Restore everything afterwards; the repo must end with both binaries present.
- Make the resolved variant OBSERVABLE: export a `resolvedVariant()`
  (or equivalent) from `loader-state.js` and log the chosen
  binary at load in one concise line. No silent fallbacks.

### 4. Perf regression: cargo-registry grep case
Root-cause why native grep is 2x slower than rg on the cargo-registry
content case while being faster everywhere else. If algorithmic (e.g. SIMD
path not triggering on that input class), fix it. If inherent, document with
numbers in the harness README. Either way the nightly bench must report the
case honestly.

### 5. Bench green
- Run `bun scripts/bench-guard.ts --update` in `packages/coding-agent` to
  capture the boot baseline on THIS machine, then verify the guard passes.
- Run the full `/home/toxic/bench-run.sh` end-to-end; every suite must exit 0
  or have a documented, committed reason it cannot.

### 6. Reporting
Emit a `DIFFERENTIAL <suite> pass=x fail=y` summary in the same parseable
style as the bench log, and leave a `test/differential/README.md`
explaining how to run the harness and what each reference is.

## Acceptance criteria
- `bun test test/differential/` green: zero output-equality failures.
- Fallback chain proven by simulation (commands + outputs recorded in the
  final report).
- `bench-run.sh` fully green.
- Everything committed and pushed to sovereign `origin/main`.
  NEVER force-push. NEVER touch `evmts/super-ralph`.

## Constraints
- Repo root: `/home/toxic/sovereign` (run ralph with `--cwd` there).
- Unique scratch dirs under `/home/toxic`; never shared `/tmp` paths.
- PUSH EVERYTHING. DONT EVER REVERT. Patch forward only.
- Shells are plain bash on awrawr-pc (Arch). bun at `/home/toxic/.bun/bin/bun`.
- If the model-call route (flock proxy) is broken, say so in the first
  report line instead of silently stalling — do not burn hours on it.
