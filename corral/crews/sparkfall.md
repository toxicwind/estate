---
crew: 'sparkfall'
scope: 'OPERATION SPARKFALL: mirror entire Dropbox (629 files/15.8MB) to yote, organize+rename, audit/fix 23 repo candidates, push working repos to GitHub private, push organized tree back to Dropbox'
owner: 'Volt (electric storm-fox)'
status: 'DONE except phase 5 -- commits c4120e83a826 (manifests); 20 repos pushed private to toxicwind/*, 2 deduped, 1 quarantined'
order: 38
registered: '2026-09-30'
updated: '2026-09-30'
---

# sparkfall

Per-crew ownership record. Edit the frontmatter above; the section 2 table in
docs/fleet-knowledgebase.md is generated from these files -- do not edit it by hand.

## 2026-09-30 -- Dropbox mirror + organize + audit (mostly DONE)

- Full Dropbox mirror: 4 shards (A 96f, B 301f, C 104f, D 128f), 629 files /
  15,833,340 bytes, sha256-verified per shard, exact match vs inventory.
  Mirror at /home/toxic/dropbox-mirror/ (shards pristine, organized tree at
  organized/).
- Phase 3 (organize): /home/toxic/dropbox-mirror/organized/ -- repos/ (23 renamed),
  docs/, misc/, bundles/. old-to-new-manifest.json maps all 895 inventory paths.
- Phase 4 (audit): 20 repos pushed PRIVATE to toxicwind/* (all build/test green,
  READMEs rewritten, secrets greps clean, PII anonymized). 2 deduped
  (telemetric-runtime-oracle already in ranch/corral; dualspace-ast-bm25-v2 merged
  into v1). 1 QUARANTINED: metaclaw-runtime (auto-approves Sentinel HITL egress
  approvals, persists session/auth tokens, JWT-shaped token in test) -- needs
  Chris's explicit call before any push.
- Manifests in ranch/spark/manifests/: dropbox-inventory.json, shard manifests,
  old-to-new-manifest.json, repo-registry.json (23 entries), audit-batch-1..4.json.
- Real bugs fixed: doubled-backslash regex breaking disclaimer matching (3 engines),
  175 tsc errors -> 0 in hyper-racer, pure-TS ChaCha20-Poly1305 fallback (RFC 8439
  verified), aerosol-deposition math bug in phytovapor.
- OPEN phase 5: push organized tree back to Dropbox + renames. BLOCKED on Chris
  granting the Dropbox content.manage scope:
  https://agent.meta.ai/connectors/dropbox/scope/content.manage/add
  (move/create_folder/create_file all return scope_status: not_granted).
