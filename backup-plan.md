# BACKUP-FORWARD AUDIT + CONSOLIDATION PLAN (2026-10-28)

Author: tau. Goal: 100%-sure clean of `/home/toxic/estate` ghost; classify the 195G
backup trees (`~/archive/*`); cherry-pick irreplaceable crypto/wallets + docs FORWARD
into `/home/toxic/pens/estate/`, then delete the disposable backup content.

## Principle (per architect)
- Do NOT lose crypto wallets / pgp / ssh / api keys. Live homes (`~/.gnupg`, `~/.ssh`,
  `~/.local/share/keyrings`, secretsmith) are the SSOT; backups hold stale + some
  ONLY-surviving copies (id_estate_sign, openfang, phone id_ed25519, root-ca-key.pem).
- IRREPLACEABLE secrets get copied into `pens/estate/products/backup-recovery/` (NOT
  `~/sovereign` — that was the retired name + a ghost-risk like estate).
- Classified via qdrant `estate_sweep` + `backup-inventory` collections (chunked upsert).

## Backup trees (195G total)
- `~/archive/home-dirs-2026` 130G — snapshot of old home: secrets, .local/share (76G),
  .local/state, .vscode, nuclei-templates, doc-markdowns
- `~/archive/detached-2026`  18G — staging/secret-scan leftovers
- `~/archive/estate-clone-20261028` 42G — the old estate checkout (6000+ files, has
  doorbell key, grafana, dotfiles)
- `~/archive/` root  4.9G — misc tar.gz (backup-pre-remake), archive dirs

## Categories (2794 inventory rows via qdrant)
- SECRET/WALLET: 47 rows — MUST-PRESERVE (below)
- DOCS: 112 rows — CONSOLIDATE FORWARD into pens/estate/docs + products
- app-config: 85, build-cache: 33, bin-dist: 10 → drop (reconstructable)
- git-checkout: 20, stale-temp: 320, misc: 2167 → drop (or archive tar if borderline)

## IRREPLACEABLE SECRET SET (copy → pens/estate/products/backup-recovery/)
- .ssh/id_estate_sign + .pub, config, known_hosts, authorized_keys
- .gnupg/ (2 pgp secret keys C49D, CC64; trustdb; public-keys.d; revocs)
- .local/share/keyrings/*.keyring (Default_Keyring, user.keystore)
- .local/share/openfang/*.keyring + stake-registry control.key + forge/scout keys (MISSING live)
- phone-grab/id_ed25519(.txt/.pub) + root-ca-key.pem + moonbox-portal_rsa_key.pem
- .secrets.graveyard-20260914, .secrets.dir.bak (GEMINI_EAP_KEY_0..6), .secrets-backup-20260930
  (arlockworks-core, moonbox-live, moonbox-intel-v2, zed-byok-config)
- .docker/.token_seed, .9router/jwt-secret, .mitmproxy/*.pem
- estate-clone: doorbell.tailc9ac71.ts.net.key

## STEPS
1. [x] Full-disk sweep (1144 refs) + qdrant index; lease-guard enforced; grafana root-cause fixed
2. [ ] Relocate sovereign crypto stash → pens/estate/products/backup-recovery/
3. [ ] Copy remaining irreplaceable secrets forward
4. [ ] Consolidate DOCS forward into pens/estate/docs + products per-dir
5. [ ] Delete disposable backup subtrees (build-cache/git-checkout/stale-temp/misc) via rm
   (archive-then-delete: keep a manifest of deleted content)
6. [ ] Verify: estate absent, lease ok, crypto checksums match, daemons healthy
7. [ ] Commit + push (estate + ops + barn), update squawk todo