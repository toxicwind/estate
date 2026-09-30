---
crew: 'slate'
scope: 'SQUAWK CLI + WARDEN (stream-C): fail-open CLI reads — cell-local last-good cache lane on total bridge loss + load_profiles stale-cache fallback; ferrous-warden (estate-reconcile) alert dedupe/coalescing so the 9/25 ~70-posts/90s flood can never repeat; _squawk seq via seq_alloc.py'
owner: 'ember'
status: 'DONE (2026-09-30) -- commits 9eb22036d7 (kb register) + 365fa3ecc9 (squawk CLI fail-open cache lane) + f97e987e23 (ferrous-warden dedupe); origin/main verified via git ls-remote; warden watch daemon hot-deployed+restarted'
order: 96
registered: '2026-09-30'
updated: '2026-09-30'
---

# slate

Slate the otter-wolf — squawk-cli/warden lane (Ember's crew).

1. Squawk CLI fail-open reads: Nightjar's 23:40 dual-lane (file vs feed) hardening diffed, not duplicated. Building the third lane: cell-local last-good read cache served (loudly bannered stale) when the bridge is totally down, plus stale-cache fallback for runners.yml profiles.
2. Ferrous-warden (bin/estate-reconcile) alert dedupe: identical alerts coalesced within a 10-min window, repeats counted not posted; a single summary goes out on state change or window expiry. Never silent — the warden always speaks, just once per state.

Per-crew ownership record. Edit the frontmatter above; the §2 table in
`docs/fleet-knowledgebase.md` is generated from these files — do not edit it by hand.
After changing this file, run `bun projects/ops/bin/kb-rollup.ts`.
