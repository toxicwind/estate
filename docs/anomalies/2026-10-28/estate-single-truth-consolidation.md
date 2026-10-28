

## 2026-10-28 evening arc — anomalies #53-#60 (all verified with live probes this session. Charter: every anomaly gets a capability-contract test before its fix is trusted.)

|#|Anomaly|Essence|Fix (committed)|
|---|---|---|---|
|53|Secrets committed to repo|backup-recovery stash (GEMINI_EAP_KEY_3 etc.) got folded into estate main; GitHub push-protection rejected|stash → /home/toxic/estate-secrets-recovery (outside repo), history rewritten clean, pushed 7f451eb2b5|
|54|Secrets triple-truth|kryptos master stale since Oct-16 init while barn/secretsmith held Oct-24/25 features (label-scoped --replace, alias-map, TS runtime); estate/services/keygate a third copy|cherry-pick barn→kryptos, retire barn+keygate+vendored ranch copy; kryptos v1.0.0 f6e7ef7|
|55|Orphan keypool|:25109 served by bun with DELETED exe, cwd inside archived estate clone, ghost /home/toxic/estate defaults → boot ENOENT after restart|defaults → pens, pitchfork restart, 7 pools + keyring-SSOT live; a411783|
|56|~/.openfang resurrected|kappa manifest (moved-3) carried state_dir→~/.openfang; rig spawn recreated the retired path|retarget → ~/.rig/workspaces, 0 refs verified|
|57|Kairos inert in every shell|.bashrc sourced /home/toxic/estate/bin/bash-2s-shim.sh (ghost) and BASH_ENV was disabled pre-kairos-fix|shim → pens/olympus/products/kairos/shim.sh in .bashrc+.bash_profile; bash -i proves SHIM-LOADED|
|58|--app keypool: 0 keys|pool keys lacked service=keyring attrs; anomaly #16 pattern|D-Bus SetAttributes with Variant-wrapped attrs (dbus-next exports no SessionBus/MessageBus); 12 keys stamped, stanza wired to secretsmith env --app keypool|
|59|loadSecrets merge order|ambient process.env overrode the secrets file before quote-stripping was observable → 2 RED TDD tests|file wins over env, keyring gap-fill last; 46/46 green e19f114|
|60|Quota-blind routing|keypool had no $160/day pro-plan ledger; reasoning-budget trap risk on long loops|QuotaTracker TDD (5 tests: accumulate, UTC-midnight rollover, restart-safe, over-budget flag) + GET /quota live e9ba53d|
