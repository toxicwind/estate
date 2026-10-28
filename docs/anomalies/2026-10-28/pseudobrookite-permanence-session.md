# 2026-10-28 pseudobrookite + permanence + swarm-cancel session (tau) — verified fixes + root causes

**Root-cause chain (one paragraph):** The session began as abort-forensics
(collect tau's aborted sessions) and recurred through five architect
interjections that each re-scoped the goal: dangling-work→skills, save-all
meta-permanence, pens hyper-master recalibration, hyper-tailrec todo
recursion, and finally swarm cancellation. Core discoveries: (a) tau session
JSONL records tool calls in `custom` records (`tool_execution_start`), not
`message.content` tool_use — 93 ask-uses mined once the shape was right;
(b) Bun.spawn signal-kills direct-execve git on this estate (kairos
enforcement) → route through `bash -c`, and `Subprocess.exitCode` reads null
even on success → `await p.exited`; (c) `git rev-parse` in a nested product
dir silently adopts the parent pen repo → detect `existsSync(<dir>/.git)`
first; (d) the swarm's freeinference saturation was self-inflicted: swarm-10
probed 542 models × 2 passes at 90-way concurrency through a de-facto
1-lane provider queue — anomaly #4 (observer effect) and #15 (per-model
strikes) both violated by design.

**Fixes (repo + commit + verification):**
- toxicwind/pseudobrookite @ 27ca270, 123e3ea, 4d9cf35 — geode product: pseudocompiler (11 tests green, typecheck clean), save-all/live-audit/green-blue/install-tau-surface primitives, remy pre-subagent runner, REQUIREMENTS §8/§9 subagent enforcement; live analysis run: 1215 tokens, 8 workers, 5 narrator claims.
- toxicwind/olympus @ 3395c3a — mobile-autocorrect estate lexicon (probe: `yote` survives, `theh→they` corrects).
- toxicwind/estate @ 281b4d1108 (merge), 009d4f9694 — pens-master docs mirrored, unrelated-histories merge resolved 12 conflicts (took origin/main's canonical AGENTS/renames), pushed main (gh-api verified sha match).
- toxicwind/geode @ 3bf7095 — repo CREATED (remote was a 404 ghost), README row + bornite WIP fold-forward pushed.
- toxicwind/pens @ b3d97ef — peer fold-forward, clean.

**New tools:** save-all.ts (branch→tmp→micro-merge→push, forward-only), live-audit.ts,
deploy-green-blue.ts, install-tau-surface.ts, remy.ts, pseudobrookite analyzer CLI.
**Managed skills minted:** save-all-micro-merge, live-audit-to-folders,
goal-todo-recursion, ask-adhd-questions, master-orchestrator-estate.

**The lessons (do not regress):**
1. Route git through bash -c; await p.exited; never trust rev-parse in nested dirs.
2. Swarm probes MUST respect single-lane observer effect (anomaly #4): cap concurrency, honor strikes (#15). 90-way races starve the shared queue.
3. Never hot-wire a tau extension into the live session — installer + restart.
4. Session JSONL: tool calls live in `custom` records; exit records define abort status (no session_exit = hard kill).
5. save-all before yielding, every milestone. Aborted sessions eat unpushed work (24 in 2 days).
6. ffs over raw find/grep; no banned shell patterns; persist full outputs.
