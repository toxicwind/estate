# D-2026-10-28 — estate single-truth cutover + rig/kryptos consolidation

All items verified with live probes / real traffic this session.
Charter: every anomaly gets a capability-contract test before its fix is trusted.

## #48 Estate dual-truth checkout (the recurring down-daemon root)
- **Symptom**: daemons repeatedly down; /home/toxic/estate kept re-appearing; lease FAIL live at 15:27.
- **Root cause**: estate was BOTH git checkout AND runtime home (~/.tau 87G, ~/.config 4.9G symlinked into it); daemon launchers + estate-reconcile + grafana-mesh hardcoded ESTATE_ROOT:-/home/toxic/estate — every (re)start re-materialized the ghost.
- **Fix**: runtime homes relocated to real dirs (same-fs mv); all daemon scripts perl-swept to pens/estate (estate 364b68ddf9); estate-reconcile ESTATE_ROOT default fixed (ops ed4d73e); lease-guard fails if estate exists in ANY form.
- **Contract test**: bin-contract-audit green 423+25 ok; grafana restart → estate stays absent; data writes to pens/estate/grafana.

## #49 openfang→rig half-finished cutover
- **Symptom**: ~/.openfang AND ~/.rig both live; fleet-join wrote .openfang; estate/rig daemon STOPPED (fleet API :25196 dark).
- **Root cause**: rename scripts ate RENAME-AUDIT.md itself ("rig → rig", "symlink ~/.rig → ~/.rig"); cutover abandoned at 90%.
- **Fix**: state migrated to ~/.rig (agents/stake-registry/key-pool/13 workspaces), legacy home archived; fleet-join repointed (rig API/lane); estate src file+code cutover (services/rig.ts, lib/rig_api.ts, src/rig/, deploy/rig_providers.ts; ZERO openfang refs); estate/rig STARTED (api/agents 200).
- **Contract test**: rig :25196/api/agents → 200; grep openfang src/scripts/stack → 0 files.

## #50 kryptos mastership (secrets SSOT)
- **Symptom**: THREE copies (ranch/kryptos vendored, olympus/products/kryptos stale-since-init, barn/secretsmith ahead with TS runtime + label-scoped features); keygate vendored estate copy diverged.
- **Root cause**: half-migrations left every copy owned by a different repo; no master.
- **Fix**: barn's newer code cherry-picked INTO kryptos (label-scoped --replace, exec/env, alias-map, TS runtime, tau-auth-sync); keypool state ingested; keygate + ranch/kryptos + barn/secretsmith retired; LICENSE/MIT + star-ready README + v1.0.0 tagged.
- **Contract test**: secretsmith --help full CLI; keypool 41/41 TDD green; 7 pools loaded; :25109/health 200.

## #51 loadSecrets merge-order bug (quote TDD red)
- **Symptom**: 2 RED tests (strip single/double-quoted secretsmith env values).
- **Root cause**: process.env loop overrode file record before quote-stripping observable; test env pollution via harness-inherited real keys.
- **Fix**: merge order ambient env → file (local override) → keyring gap-fill; prod-neutral (file gone post-cutover).
- **Contract test**: bun test 41 pass 0 fail (99 expects).

## #52 git credential helper unconfigured
- **Symptom**: "could not read Username for 'https://github.com'" mid-session pushes.
- **Fix**: `gh auth setup-git` (credential.helper = gh auth git-credential, permanent).
- **Contract test**: ranch diverged-main rule-4 merge + push OK (b47c454bc).
