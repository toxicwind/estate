# estate-scripts ghost path in rig-kernel (D-2026-10-28 #51)

## Symptom
rig-kernel/src/kernel.rs referenced `/home/toxic/estate-scripts/config/rig-25196.toml` — a path that never existed (/home/toxic/estate-scripts absent). estate-scripts was a stale ghost brand, not rig's live config home (~/.rig/ is).

## Root cause
Leftover from the pre-rig rebrand where config lived at estate-scripts/config. The rig-kernel unit tests (test_resolve_reload_config_path_*) hardcoded this path as a test fixture; agent persona files (coyote.toml/system.md, oracle.toml) described agents as "first-class estate-scripts service" prose.

## Fix
Kernel test fixtures → `/home/toxic/.rig/config-25196.toml` (rig's live config home); agent personas rebranded estate-scripts→rig; RENAME-AUDIT.md updated with estate-scripts ghost cutover note. Committed 1ce84c5 and pushed forward on rig main (after the consolidated reconstruction).

## Contract test
grep estate-scripts in rig source → 0 occurrences in non-test live code (agent prose fixed; test fixtures now ~/.rig). Push verified: remote main == 1ce84c5.
