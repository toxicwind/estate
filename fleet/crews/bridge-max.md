---
crew: 'bridge-max'
scope: 'Maximal bridge exec layer: multitask dispatch (POST /exec-multi, yote-conn multi), detached background dispatch (POST /exec-bg, GET /bg, yote-conn bg/bg-status/bg-list), bg-kill (POST /bg/<handle>/kill, yote-conn bg-kill), MCP exec_multi/exec_bg/bg_status tools; reap-on-query stale jobs (pid-reuse-safe /proc cmdline check)'
owner: 'Ember'
status: 'DONE (2026-09-20) -- commits 25679fa5c0 (core), ae890221a2 (marker), efe63f8115 (reap-on-query + bg-kill), f59949ae0c (follow-up marker); connector v2.1 live (daemon PID 40978); kill path live-tested (SIGTERM process group -> stale, zero survivors)'
order: 30
registered: '2026-09-20'
updated: '2026-09-29'
---

# bridge-max

Per-crew ownership record. Edit the frontmatter above; the §2 table in
`docs/fleet-knowledgebase.md` is generated from these files — do not edit it by hand.
After changing this file, run `bun projects/ops/bin/kb-rollup.ts`.
