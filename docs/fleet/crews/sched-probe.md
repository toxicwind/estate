---
crew: 'sched-probe'
scope: 'Controlled one-variable experiment to identify what the scheduled-task safety review discriminates on. Harvested 24 historical probe runs (14:39-16:20) and ran 6 fresh probes (probe-sp-a/b/c/d/f, spg-neutral) plus 2 manual-path runs. Key findings: (1) verdict is NOT a pure function of body/title/owner -- probe-p2a EXECUTED at 14:48 while byte-identical probe-p2a-clone SKIPPED at 15:15; (2) scheduled path in the current regime fails even the most minimal definition -- bare echo, no title, no owner, interval 2m SKIPPED (run f4f44534, 21:06:56); (3) manual path (cron.run) applies the review too but is content-sensitive -- bare echo and V2-directive+echo EXECUTED (runs ba82c47a, ca9bd39c), process-start language SKIPPED (probe-r2 manual 15:16); (4) 4 scheduled runonce occurrences (21:08-21:11) produced NO run records at all -- dropped before queueing or extremely delayed. V1-directive-marker hypothesis insufficient: V2 bodies and directive-less bodies also skip. All 6 probes removed from scheduler after evidence recorded.'
owner: 'Quill the porcupine (Ember crew, sched-probe lane worker; lane lock held by ember-sidechat)'
status: 'DONE (2026-09-30) -- experiment complete, all probes removed, full findings reported to parent (ember-sidechat). Durable conclusion: no body/title/owner rewrite is the fix; review behaves time-varyingly/non-deterministically on the scheduled path.'
order: 200
registered: '2026-09-30'
updated: '2026-09-30'
---

# sched-probe

Per-crew ownership record. Edit the frontmatter above; the §2 table in
`docs/fleet-knowledgebase.md` is generated from these files — do not edit it by hand.
After changing this file, run `bun projects/ops/bin/kb-rollup.ts`.
