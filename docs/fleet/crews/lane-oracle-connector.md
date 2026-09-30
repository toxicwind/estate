---
crew: 'lane-oracle-connector'
scope: 'Oracle intake adoption (verified complete, zero oracle code changes) + yote-connector canonicalization: yote-conn promoted to the single canonical operator path'
owner: 'lane-oracle-connector (Ember''s crew)'
status: 'DONE (2026-09-20) -- sovereign-projects main `0f4f3bdadf032d8030db2bcab928efbf93dbb739` (ls-remote verified): (A) oracle adoption PROVEN live — `agents/oracle-market/docs/ADOPTION-PROOF.md`: intake unit test OK (6 routes), live TASK (ledger settled, winner bidder-scout), live REJECT, live DIRECT; ORACLE_INTAKE=1 in running process env; no oracle source touched. (B) canonicalization — bg-tail finished end-to-end (`bg-status.py` offset args -> `stdout_b64/stdout_soff`, daemon `GET /bg/<handle>?soff=&eoff=`, CLI resume/negative-offset/tails-fallback; fixed empty-chunk resume + stdout ordering bugs caught in live test); `/exec-bg` `timeout_s` + `workdir` now forwarded to bg-run.py (both silently dropped before — workdir ran in /home/toxic regardless); `projects/bridge/hatch/yote-conn` updated to the live CLI (169->222 lines) and added to `deploy-cell.py` FILES with chmod 755; `bexec` -> thin `yote-conn exec` shim (adopted as `hatch/bin/bexec`); `fleet-classify` -> yote-conn transport (raw exec.py fallback kept); `swarm-{eject,resume,watchdog}` DELIBERATELY keep raw exec.py (emergency path when 18301 is down — commented); bridge README canonical-path policy section. Deployed: daemon restarted via deploy-yote-connector, health ok (transport ws); live-tested bg-tail resume, workdir (/tmp file created), timeout (state=timeout, exit -1), bg-kill (SIGTERM, exit -15).'
order: 56
registered: '2026-09-20'
updated: '2026-09-29'
---

# lane-oracle-connector

Per-crew ownership record. Edit the frontmatter above; the §2 table in
`docs/fleet-knowledgebase.md` is generated from these files — do not edit it by hand.
After changing this file, run `bun projects/ops/bin/kb-rollup.ts`.
