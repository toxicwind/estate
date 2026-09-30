---
crew: 'benchlink'
scope: 'router benchmark inventory + bench-based wiring: bench-priors.json generator (GuideLLM v3 quality + MODEL-MAX liveness/latency + router-proof availability signal) feeding sovereign-router Elo prior seeding; hot-reload via /admin/reload + SIGHUP (untouched providers keep live-learned Elo); live outcomes keep updating Elo'
owner: 'benchlink (Ember''s crew)'
status: 'DONE (2026-09-21) -- commit da8fd5ed7a: gen-bench-priors.py + bench-priors.json (openrouter 1078, llama-swap 1025, rest 1000 unbenched), router_matrix.ts Elo prior seeding + hot-reload-safe applyBenchPriors, router.ts /admin/reload+SIGHUP hook; 20/20 bun tests pass; deployed to :25104 via owned restart, /status shows priors, /admin/reload verified live'
order: 76
registered: '2026-09-21'
updated: '2026-09-29'
---

# benchlink

Per-crew ownership record. Edit the frontmatter above; the §2 table in
`docs/fleet-knowledgebase.md` is generated from these files — do not edit it by hand.
After changing this file, run `bun projects/ops/bin/kb-rollup.ts`.
