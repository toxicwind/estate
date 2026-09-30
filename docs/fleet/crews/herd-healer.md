---
crew: 'herd-healer'
scope: 'Event-driven dead-peer self-healing for the herd router (per-peer FSM, EWMA, single-flight half-open)'
owner: 'Ember'
status: 'DONE (2026-09-20): feature 837810e422, merge abe7bbb65d; re-verified live 2026-09-20 by ember-edge-selfheal (edge-forge #3 re-dispatch — coordinator claim of "no commits" was wrong, feature already on main): live binary 2026-09-20 17:04 contains peer_circuit_open + GET /peer-health; :25100 /peer-health serving per-peer FSM (healthy, threshold 8); projects/herd/scripts/probe-peer-health.sh ALL ASSERTIONS PASSED (weighted ejection, fail-fast 503 peer_circuit_open with backend untouched, half-open probe on real traffic, readmission, 200-empty weighted re-ejection); supervised herd PID 3124908 (started 17:24) runs the feature binary'
order: 21
registered: '2026-09-20'
updated: '2026-09-29'
---

# herd-healer

Per-crew ownership record. Edit the frontmatter above; the §2 table in
`docs/fleet-knowledgebase.md` is generated from these files — do not edit it by hand.
After changing this file, run `bun projects/ops/bin/kb-rollup.ts`.
