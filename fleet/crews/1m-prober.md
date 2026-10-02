---
crew: '1m-prober'
scope: 'Long-context engagement probe (oracle verdict 12097, mission 4e621a18): needle-in-haystack retrieval at 100k/500k/1M tokens through the nvidia keyed lane (nemotron-3-super-120b-a12b, nemotron-3-nano-omni-30b-a3b-reasoning) and the openrouter :free nemotron ID; results recorded in ast_matrix.db requests (strategy=longctx-probe); probe script tools/sovereign-router/probes/long-context-probe.py'
owner: '1m-prober (Ember crew, worker under coordinator 4e621a18)'
status: 'DONE (2026-09-21) -- sovereign-projects 49c17bb9fd (probe script + 13 run JSONs + RESULTS-2026-09-21.md; keyed nvidia nemotron-3-super-120b-a12b 1M needle retrieval PASSED accurate 41.4s; openrouter :free capped 262144 tokens verified; lane flapped 503 ~40min mid-probe)'
order: 62
registered: '2026-09-21'
updated: '2026-09-29'
---

# 1m-prober

Per-crew ownership record. Edit the frontmatter above; the §2 table in
`docs/fleet-knowledgebase.md` is generated from these files — do not edit it by hand.
After changing this file, run `bun projects/ops/bin/kb-rollup.ts`.
