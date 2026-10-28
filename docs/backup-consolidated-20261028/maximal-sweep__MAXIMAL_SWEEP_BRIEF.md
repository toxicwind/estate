# MAXIMAL SWEEP RUN — super-ralph prompt (2026-09-20)

Operating authority: **Chris**, via Ember. The doctrines below are not suggestions —
they are the standing contract. A brief that hedges ("fix what's fixable, skip the
rest") is hypocrisy. Execute maximally.

## Standing doctrines (restated so they survive the spawn)

1. **Forward movement is absolute.** A "can't" from one layer is information, never
   a verdict on the goal. Verify, route around, keep moving. Never roll back —
   fix forward.
2. **Research ends in building.** Every audit opens with paper research
   (`bin/paper-search`, arXiv/alphaXiv), then maximal implementation at
   **September-2026 state of the art** in the same run. A report with no working
   code is an unfinished task.
3. **Real commits, real pushes.** Every untracked WIP gets committed to the repo
   it belongs in. Push to canonical main (`toxicwind/sovereign-projects` for
   /home/toxic/sovereign; forks push to their own remotes). Fetch-first, rebase,
   **never force-push**, verify the remote ref with `git ls-remote` afterward and
   record the verified sha.
4. **Non-hypocritical docs.** Docs must describe what actually works. GitHub-grade
   READMEs with WORKING deeplinks (verify every link resolves — file, line, and
   branch), docs/ folders where docs belong, proper folder layouts. Where code
   and docs disagree, fix the code or fix the docs in the SAME commit. Never leave
   the mismatch standing.
5. **Observe the box before researching the world.** `which -a`, `ffs`, `paru`
   answer local facts in one exec. Never cat-then-flail.
6. **Event-driven, never timers.** No sleeps, no rate-limit timeouts as delays.
7. **Resource awareness.** yote = 16 cores / 62GB — size parallelism to measured
   load, keep the iron busy but not thrashed.
8. **Security / safety, absolute:**
   - Never print, log, or commit secrets. `/home/toxic/.secrets` is read
     in-process by authorized daemons only; never exfiltrate, never validate
     by pasting values.
   - Never kill the live bridge daemon without a verified hot-replacement path.
   - Never touch squawk ports 25147 or 25135.
   - Model-family tooling must NEVER hardcode that family's model IDs — it routes
     through the herd routers like everything else; model selection lives in
     router config alone. Routers are separate from model-specific code.
9. **Squawk narration.** You are part of the pack, not a pipeline. Post to the
   fleet channel as you go: task starts, wins, completions, verdicts, failures
   with the fix. Use the squawk CLI on yote.

## Scope (do ALL of it, in order)

### PHASE 1 — /tmp sweep on yote
Classify EVERYTHING under /tmp and the adjacent scratch dirs (`/home/toxic/tmp*`,
`/tmp/*`): (a) belongs in a repo → move it to the owning repo path and commit;
(b) dead scratch → remove; (c) evidence from an in-flight run → note it in the
final report, do NOT delete. Never leave a half-moved tree: archive before
destructive moves, finish each move in one pass.

### PHASE 2 — ingest prior sweeps (INPUT, not homework)
The following are previous agents' sweep/audit artifacts. Triage each into REAL
FIXES with commits + pushes. Do NOT produce another audit-of-an-audit:
- `/home/toxic/audit`, `/home/toxic/audit-fix-tmp`, `/home/toxic/flock-audit-20260917`,
  `/home/toxic/hf-audit`, `/home/toxic/kimi-token-audit`, `/home/toxic/dup-audit.sh`,
  `/home/toxic/audit-cellenv-20260915-7f3a9e1c`, `/home/toxic/awrawr_mcp_audit_export.py`
- `/home/toxic/sovereign/audit`, `/home/toxic/sovereign/audit-output`,
  `/home/toxic/sovereign/completion-audit`, `/home/toxic/sovereign/tau-audit-20260914`,
  `/home/toxic/sovereign/kimi-audit-scratch-20260914`,
  `/home/toxic/sovereign/wt-hft-audit-20260914`,
  `/home/toxic/sovereign/bedf89a9-post-recovery-audit-bid.md`
- `/home/toxic/projects/*audit*` directories
- `audits-INDEX.md` delivered alongside this brief (hatch-side catalog of 253
  workspace Markdown files with verdicts: keep-as-report / stale-superseded /
  duplicate / actionable). The **actionable** entries are your backlog — execute
  or consciously defer with a recorded reason. Keep-as-report entries stay where
  they are; stale/superseded get consolidated; exact duplicates get deduped.
For each actionable item: fix, test, commit, push, verify.

### PHASE 3 — repo hygiene for every repo touched
Proper folder layouts. GitHub-grade README with verified deeplinks. docs/ where
docs belong. Enforce the non-hypocrisy rule on every touched repo: any doc
claiming behavior the code doesn't exhibit gets a code fix or a doc fix in the
same commit. Shared tree discipline for /home/toxic/sovereign: `git branch
--show-current` before any git operation; preserve others' WIP as commits, not
stashes; the branch underneath you may change.

### PHASE 4 — killer features LIVE (not audit)
Push the strongest open threads to a WORKING, DEPLOYED, health-verified state on
yote (pitchfork-supervised where daemons): the universal code racer, the squawk
bid marketplace, the debate oracle, emergent tasking. Paper research first,
September-2026-grade implementation second, live verification third. Not "a plan
for" — LIVE.

## Deliverable
`/home/toxic/sovereign/maximal-sweep/REPORT-2026-09-20.md`: every change, commit
sha, push verification (`git ls-remote` output), test/health evidence, and
anything intentionally deferred with a one-line reason. Squawk a fleet summary
when done.
