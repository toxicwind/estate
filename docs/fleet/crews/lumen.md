---
crew: 'lumen'
scope: 'Squawk feed UI readability: keeper-driven visual audit (CDP :9223) of /squawk-feed/ui at desktop 1440x900 + mobile 390x844; root-caused empty bodies (pre-HMAC msgs fail verify_on_read -> body withheld); fix = serve bodies flagged unverified + card-layout redesign'
owner: 'Lumen (Ember''s crew)'
status: 'DONE (2026-09-21) -- relay fix e5fdce9c95 (serve pre-HMAC plaintext flagged invalid, fail-closed on ciphertext; 12/12 feed tests OK), UI redesign cb6bd69f82 (cards, unverified badges, scroll-to-bottom, mobile, favicon); keeper-verified 1440x900 + 390x844, 0 console/page errors; deployed live :25135  markdown render + full bodies 0b33559ad2 (truncate dropped, escape-first md renderer, keeper-verified live)'
order: 87
registered: '2026-09-21'
updated: '2026-09-29'
---

# lumen

Per-crew ownership record. Edit the frontmatter above; the §2 table in
`docs/fleet-knowledgebase.md` is generated from these files — do not edit it by hand.
After changing this file, run `bun projects/ops/bin/kb-rollup.ts`.
