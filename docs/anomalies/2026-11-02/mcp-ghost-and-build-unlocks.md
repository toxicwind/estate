# 2026-11-02 — MCP fleet ghost paths + build-loop unlocks (retro dossier)

All items verified with live probes / real traffic this session. Charter:
every anomaly gets a capability-contract test before its fix is trusted.
(Charter from the D-2026-10-23 program — keep it.)

## 1. sccache-wraps-cc build hang (rhodochrosite release compile)

- **Symptom**: `cargo build --profile release-fast` hung ~3min at cpu=0 on
  `libsqlite3-sys` — child was `sccache cc -O2 … sqlite3.c`, wchan
  `anon_pipe_read`, 0 jiffies. Earlier runs clipped at the 60s harness cap.
- **Root cause**: cargo `[build] rustc-wrapper = "sccache"` exports
  `RUSTC_WRAPPER` into build-script env; cc crate 1.2.65 auto-prefixes C
  compiles with `sccache cc …` (documented RUSTC_WRAPPER behavior), and
  sccache 0.19.0 blocks on its server pipe for that invocation.
- **Fix**: cc 1.2.65 → 1.11.0 (jobserver polling fixes 1.8.0–1.10.0; verified
  in changelog). rhodochrosite `ec11fcd`, pushed.
- **Contract test**: from-clean `release-fast` build completes exit 0
  (libsqlite3-sys line passes, full tree 6m10s); incremental touch-rebuild
  40.15s with mold. sccache stats: 405 misses then cache hits on rebuild.

## 2. scaffold-mcp dispatched to a ghost bin dir

- **Symptom**: `scaffold_audit` via gateway → "transport closed" (then
  restart fixed transport; the real defect was below).
- **Root cause**: `eidos/mcp/server.ts` hardcoded
  `BIN = "/home/toxic/pens/toolkit/scaffold/bin"` + `cwd:
  /pens/toolkit/scaffold` — both dead (stat fails). eidos IS bun-scaffold
  (renamed); real bins at `/home/toxic/pens/ergasterion/eidos/bin/`.
- **Fix**: repointed both constants (eidos `f141003`);
  `scaffold_audit ergasterion` returns real FAIL/OK rows.
- **Contract test**: gateway `scaffold-mcp:scaffold_audit` live call —
  ergasterion audit emitted concrete findings.

## 3. Persisted thresher config carried 5 stale MCP paths (two-truth, #6/#42 class)

- **Symptom**: `mcp_config.json` pointed squawk/hatch-mcp/ast-grep/github at
  dead pre-reorg homes; safurrier at a removed vendored dir. Live gateway
  already ran corrected paths for several — config would resurrect ghosts on
  restart.
- **Root cause**: path reorg updates applied via gateway patches but not
  persisted back into the SSOT config file.
- **Fix**: estate `2acfa7a3b7` — repointed 4 to live paths, disabled
  safurrier; live gateway patched in parallel (squawk verified).
- **Contract test**: 69-upstream scan asserts **0 enabled servers with dead
  paths** (os.path.exists on command+first arg); regression python one-liner
  in recon dossier `infra/infra-forensics/mcp-ghost-audit-20261102/README.md`.

## 4. forge hf dispatch missing from the master entrypoint

- **Symptom**: `forge hf` never existed — neither the `hf` case in
  `bin/forge` nor an `oracle` subcommand in `hf/cli.ts`.
- **Root cause**: hf CLI grew after the entrypoint's last dispatch update;
  oracle (W1-W8) scratch lived in /tmp, not the product.
- **Fix**: forge `57eec27` + `497f853` — `hf` case wired, `oracle w1..w11`
  + `firewall` subcommands; experiments moved from /tmp to `hf/oracle.ts`.
- **Contract test**: `forge hf oracle w1` (0.8065/0.8171) and
  `forge hf firewall "<dsml>…"` (kind=markup, score 0.35) live through the
  `~/.local/bin/forge` symlink → entrypoint → hf CLI → module chain.