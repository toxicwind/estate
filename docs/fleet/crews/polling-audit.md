---
crew: 'polling-audit'
scope: 'Estate-wide polling audit: every timer/sleep/poll-loop on hatch + yote, classified LEGIT vs CONVERT (event-driven alternatives)'
owner: 'Shrew (Ember''s crew)'
status: 'DONE (2026-09-21) -- report docs/polling-audit-2026-09-21.md, commit ce3f867754821f132709163470ac394603e297a8; 7 CONVERT / 17 LEGIT / 10 already-event-driven / 2 ambiguous; top converts: paper-poller 30s->inotify, stash-guard 90s->inotify, squawk-monitor 5m->subscribe'
order: 94
registered: '2026-09-21'
updated: '2026-09-29'
---

# polling-audit

Per-crew ownership record. Edit the frontmatter above; the §2 table in
`docs/fleet-knowledgebase.md` is generated from these files — do not edit it by hand.
After changing this file, run `bun projects/ops/bin/kb-rollup.ts`.
