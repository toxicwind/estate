---
crew: 'tau-hyperfix'
scope: '`/home/toxic/.tau` audit; dynamic skill loading; skills symlink; `skillful`; `tau audit`; `tau tmux` experiments'
owner: 'Ember'
status: 'DONE (2026-09-21) -- audit 14 pass / 0 warn / 0 fail; all 3 stale warnings fixed in tau-audit.sh and pushed to origin/main: (1) branch-behind demoted to INFO (canonical ref is origin/main; shared tree never touched), (2) dirty-WIP replaced by content-vs-main drift check (untracked on-main files = branch-lag detritus, mode-only noise ignored; synthetic new-file test still warns), (3) hardcoded :8379 replaced by WS_EXEC_PORT read from pitchfork [daemons.awrawr-ws-exec] (=25204). Commits b3a509d8e3 + f8d303dfbd, remote-verified. tmux lifecycle (new/ls/capture/kill) OK, `tau launch -p` -> TAU_OK (~15s), dist/omp healthy, install.sh idempotent. Frontmatter sampling warning fixed at the source: rust-browser-pilot description: moved up (gk-live-gear e4d72e3). Launcher deliverables byte-identical on origin/main; historical caveat stands: local commits a356d831ee06 / 3c8c5566cf are orphaned and NOT canonical SHAs -- nothing left to push.'
order: 10
registered: '2026-09-21'
updated: '2026-09-29'
---

# tau-hyperfix

Per-crew ownership record. Edit the frontmatter above; the §2 table in
`docs/fleet-knowledgebase.md` is generated from these files — do not edit it by hand.
After changing this file, run `bun projects/ops/bin/kb-rollup.ts`.
