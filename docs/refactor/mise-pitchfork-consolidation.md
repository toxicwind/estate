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
- **P3a**: create pens-root mise.toml; drop redundant pen pins (barn/geode
  1.4.4 → inherit; olympus/ranch/kelpie latest → inherit + keep tasks).
- **P3b**: bump 5 stale 1.4.2 pins + phone-sentinel 1.4.3 → root default;
  repoint doorbell-oauth-edge run cmd to mise-resolved bun.
- **P3c**: migrate tmp/olympus-namespace daemons from estate monolith to
  their pens; regenerate monolith via pitchfork-compose; verify
  `pitchfork status` green after each batch.
- **P4**: restart affected daemons, `mise resync`, commit each repo
  straight to main, update this doc with results.

## Blast radius
Config-only; every change reversible via git (each pen/product is a repo).
Daemons restart under pitchfork supervision. No credentials, no boot
path, no remote infra touched.
