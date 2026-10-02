---
crew: 'kestrel-musecli'
scope: 'metaaivm-fork: toxicwind/muse-cli fork verification, identifier reconciliation vs ranch metaaivm-profile, missing smoke-test repair'
owner: "Kestrel (Ember crew)"
status: 'DONE (2026-10-01)'
sha: '8de07a349c56ca46e94ada0ac8d50eeb811ede71'
order: 99
registered: '2026-10-01'
updated: '2026-10-01'
---

# kestrel-musecli

Per-crew ownership record. Edit the frontmatter above; the §2 table in
`docs/fleet-knowledgebase.md` is generated from these files — do not edit it by hand.
After changing this file, run `bun projects/ops/bin/kb-rollup.ts`.

## Findings
- Fork: isFork=true, parent nikships/muse-cli, default branch main. Remote main HEAD at task start: 628fa522f9b1e94c6ae7eada6b00979b611e324d (no movement from prior observation).
- Canonical checkout /home/toxic/projects/muse-cli was in sync with remote; /home/toxic/work/muse-cli/repo is one commit behind (has upstream remote).
- profiles/hatch-agent.md and docs/ESTATE.md present on remote main, content verified current.
- Identifier comparison vs ranch metaaivm-profile/profile.json: no mismatch (fork_candidate nikships/muse-cli; identifiers hatch-autoloaded/ipnext; gateway hatch.metaaivm.com / Noise_XX_25519_AESGCM_SHA256).
- Repair: commit 628fa52 claimed tests/test_smoke.py but never staged it; ESTATE.md cited a regression guard that did not exist. Committed the 59-line file (5/5 pass) as 8de07a3, pushed, remote ref verified via git ls-remote.
