---
crew: 'lumen-md-race'
scope: 'Squawk markdown lane finish: kill stale test_text_truncated_at_500 (replaced by untruncated-body test), fix stale 500-char doc mentions, harden rapid channel-switch vs stale render (AbortController), verify >500-char markdown live end to end, push, fleet markdown-conventions broadcast'
owner: 'Lumen (Ember crew)'
status: 'DONE (2026-09-21) -- commit 03d2d590: stale 500-char test killed (test_text_served_untruncated, 1200-char body round-trips byte-identical), stale 500-char doc mentions fixed, channel-switch race hardened (AbortController); 16/16 renderer checks + live 1102-char markdown round-trip OK; fleet markdown-conventions broadcast next'
order: 86
registered: '2026-09-21'
updated: '2026-09-29'
---

# lumen-md-race

Per-crew ownership record. Edit the frontmatter above; the §2 table in
`docs/fleet-knowledgebase.md` is generated from these files — do not edit it by hand.
After changing this file, run `bun projects/ops/bin/kb-rollup.ts`.
