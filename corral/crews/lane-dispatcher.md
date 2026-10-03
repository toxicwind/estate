---
crew: 'lane-dispatcher'
scope: 'canonical dispatcher/ledger build: mission/coordinator/worker/relay IDs, lifecycle+result tracking, direct-Chris precedence, duplicate-admission locks, append-only hash-chained relay records, artifact/commit aggregation, automatic relay archival, exactly-four-audit-lanes enforcement'
owner: 'lane-dispatcher (Ember''s crew)'
status: 'DONE (2026-09-21) -- impl commit `c6e9acd9b3f2993d9e55617e2596a2399d9df7f5` on origin/main (ls-remote verified): `projects/ops/dispatcher/` (fleet_dispatch package: ledger/ids/admission/relay/dispatcher, bin/dispatch CLI, 24-test stdlib suite ALL PASS, README); projects/ops/README.md dispatcher entry; .gitignore state/ exclusion. Restart proof: E2E CLI drill + TestRestart (new Dispatcher continues IDs/locks/ledger chain). Triage folded in: sovereign-chat dispatch.ts = internal lease queue (below this layer); corral/dispatch_fallback.py = transport fallback (complementary); oracle intake = triage front door (this is the dispatch side).'
order: 43
registered: '2026-09-21'
updated: '2026-09-29'
---

# lane-dispatcher

Per-crew ownership record. Edit the frontmatter above; the §2 table in
`docs/fleet-knowledgebase.md` is generated from these files — do not edit it by hand.
After changing this file, run `bun projects/ops/bin/kb-rollup.ts`.
