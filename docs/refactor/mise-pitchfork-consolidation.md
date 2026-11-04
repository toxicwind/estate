# REFACTOR: mise + pitchfork consolidation under pens (2026-11-04)

## Verified ground truth (survey 2026-11-04, ffs-based)

### Supervisor topology (how pitchfork ACTUALLY loads)
- One pitchfork supervisor rooted at `/home/toxic/pens`, discovering each
  pen's `pitchfork.toml`, namespacing daemons by pen name
  (`estate/grafana`, `geode/rhodochrosite`, `ranch/doorbell-mcp`,
  `tmp/argos-xerj-node`, `barn/thresher`).
- `estate/pitchfork.toml` is the 1045-line estate-pen config: 135 daemon
  stanzas, most unnamespaced (estate-owned), plus legacy groups
  (`[groups.mesh]`, `[groups.core]`, `[groups.agents]`).
- `pitchfork.d/*.toml` fragments exist in estate (D2 compose inputs for
  `estate-ops/pitchfork-compose`) — DUAL TRUTH with the monolith
  (anomaly #6 pattern). doorbell fragments still point at the dead path
  `/home/toxic/pens/ranch/doorbell` (product moved to
  `ranch/products/doorbell`) yet daemons run — running procs predate the move.
- Per-pen configs: `geode` (102L, 5 daemons), `barn` (98L), `fleet`/`mesh`/
  `wip` (empty stubs). Product-level `pitchfork.toml` files exist in
  barn/products/{polyglot-bun-audit,model-stats,latency-fallback} and
  fragments in kelpie/products/waterbowl + barn/products/lookout.

### mise toolchain drift (96 live mise.toml of 121 total)
| pin | count | files |
|---|---|---|
| (none — inherits parent) | 67 | most product dirs |
| `bun = "1.4.4"` | 12 | barn, geode, codeflux, kelpie pens + ww, argos, trench, recon-gallery… |
| `bun = "latest"` | 5 | olympus, ranch, kelpie pens (+tasks run/check) |
| `bun = "1.4.2"` | 5 | **STALE**: tau, tau-verify, bornite, herd, metaclaw-runtime (doorbell-oauth-edge hardcodes this path in its run cmd) |
| `bun = "catalog:"` | 4 | workspaces using a catalog |
| `bun = "1.4.3"` | 1 | ranch/products/phone-sentinel |
| `bun = "1.3.2"` | 1 | vendored test artifact (nim-repos ext_conformance) |
| `bun = "1.1.38"` | 1 | vendored artifact (hatch/kite grebe .estate-shared) |
- NO `/home/toxic/pens/mise.toml` root exists — nothing unifies the tree.
- estate/mise.toml carries env SSOT (`config/ports.env`,
  `config/rhodochrosite-ssot/route.env`, remote cache :25148) but no tools.

## Target state

1. **pens owns the toolchain root**: new `/home/toxic/pens/mise.toml`
   with `[tools] bun = "1.4.4"` (the verified estate standard) + shared
   `[tasks]` (run/check) moved from olympus/ranch pen files.
2. **Per-product mise.toml only where the product DIVERGES** (catalog:,
   pinned-for-repro builds). All 1.4.2/1.4.3 pins either bumped to root
   default or explicitly justified in a comment.
3. **Pitchfork**: pen-owned configs stay (namespacing works), but:
   - estate monolith slims down: daemons whose `dir` is outside estate/
     migrate to their pen's pitchfork.toml (barn/geode already done;
     tmp/, olympus/ pending).
   - `pitchfork.d/` fragments become the compose SSOT for estate daemons;
     monolith becomes GENERATED output of `pitchfork-compose` (kills
     anomaly #6 two-truths permanently).
   - Stale `dir` paths repaired (doorbell → `ranch/products/doorbell`).
4. **Vendored/artifact mise.toml files** (1.1.38, 1.3.2) are inside
   product repos' vendored trees — leave, they're data not config.

## Phases

- **P1 survey** ✅ (this doc's tables)
- **P2 design** ✅ (target state above)
- **P3a** ✅ DONE 2026-11-04: pens/mise.toml root created (bun 1.4.4 +
  run/check tasks); barn/geode/olympus/ranch/kelpie pen configs now
  inherit; verified 1.4.4 resolves in all five.
- **P3b** ✅ DONE 2026-11-04: bun pins removed from tau, tau-verify,
  bornite, forge/herd, metaclaw-runtime, phone-sentinel (all resolve to
  root 1.4.4). doorbell-mcp + doorbell-oauth-edge run cmds repointed to
  absolute bun 1.4.4 paths, `mise = true` dropped (anomaly #43), stanzas
  now live in ranch/pitchfork.toml (concurrent writer moved them out of
  pitchfork.d and deleted the fragments — monolith+pen-configs are the
  surviving truth). Both daemons restarted and green.
- **P3c** ⏸ handed to concurrent writer (they are actively migrating
  stanzas pitchfork.d → pen configs; do not double-drive).
- **P4** ✅ DONE 2026-11-04: all touched repos committed straight to main
  and pushed (barn bf599ae, geode e5513ba, olympus a0165d0, ranch
  2a0b65ad1+16c44ce87, kelpie 32fae97, tau 86e7ef7aff, bornite e4e32d3,
  forge 90d2076, metaclaw f202d03, phone-sentinel 1eadcde, estate de6788a).
  tau-verify was detached; fast-forwarded to main (fix was already pushed
  from detached HEAD).

## Blast radius
Config-only; every change reversible via git (each pen/product is a repo).
Daemons restart under pitchfork supervision. No credentials, no boot
path, no remote infra touched.
