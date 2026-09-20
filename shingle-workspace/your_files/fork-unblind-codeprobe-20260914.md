# Fork Unblind: sjarmak/codeprobe → toxicwind/codeprobe

**Date:** 2026-09-14 · **Version audited:** 0.14.0 · **Size:** ~84k LOC Python, Apache-2.0
**Method:** blindspot-pass → codemap (4 parallel mappers: tech, architecture, conventions/testing, concerns) → code-quality-review (strict, 5 hot files). All inspection read-only via awrawr-pc bridge; nothing committed or pushed.

## What it is

CodeProbe turns a repository's **merged pull requests into coding-agent evaluations**. Pipeline:

1. **Mine** — list merged PRs (via `gh` CLI or raw git), filter by size/quality/subsystem
2. **Reconstruct** — pin a git worktree at the merge *parent* commit
3. **Generate** — emit a task dir (`instruction.md`, `task.toml`, `tests/test.sh`, `ground_truth.json`, verifier scripts)
4. **Run** — execute one or more agent configs against the task in an isolated workspace
5. **Verify** — test script, oracle answer, or both (dual-scoring: min/mean/gate/weighted over direct + artifact legs)
6. **Record** — score plus cost, tokens, latency, tool-call counts, failure category

File-based and CLI-driven: everything is JSON + Markdown task dirs under `~/.codeprobe/{tenant_id}/{repo_hash}/`; SQLite only for the trace store. No servers, no queues. Real statistics layer (`analysis/stats.py`: Wilson CI, McNemar, Wilcoxon, Holm, Cliff's δ). Programmatic entry via `api.py:run_experiment()` alongside ~40 Click commands.

## Why it matters for tau

This is the **concrete implementation of the backgrounder's key finding** (arXiv:2606.17799 — "Coding Benchmarks Are Misaligned with Agentic Software Engineering"): score the *system* (model + harness + tools + retrieval), never the model alone. CodeProbe's design already does this:

- **Harness-swap experiment arms** — run the same tasks with a different harness/model to isolate which component moved the score (their R0 campaign ran 630 trials: 70 tasks × 3 configs × 3 seeds)
- **Fail-closed `AdapterCapabilities`** — an adapter that doesn't declare a knob is treated as supporting nothing; preflight hard-refuses experiment arms that request undeclared knobs, so A/B arms can never silently compare nothing
- **Preregistered gates** — e.g. 0.80 identical-pair-yield floor before expanding seeds; protocol-compliance exceptions documented honestly in reports

**Tau integration seam is clean.** Adapters implement the `AgentAdapter` Protocol and shell out to agent CLIs (claude/codex/copilot today), registered via `project.entry-points."codeprobe.agents"`. A tau adapter = one new class + honest capabilities + output parsing into `AgentOutput`. No fork surgery on codeprobe needed. `AgentConfig` already carries every knob a tau experiment wants: model, permission_mode, mcp_config, allowed/disallowed_tools, max_turns, cwd, timeout.

**Blocker:** tau's own engine CLI cannot boot at HEAD (`packages/coding-agent/src/config/` is entirely missing — repair-lane item logged 2026-09-14). No adapter work is meaningful until the engine boots.

## Blind spots found (unknown-unknowns)

1. **No GitHub mining module.** `mining/vcs/` has gitlab/base/http only — GitHub mining goes through the `gh` CLI with **no rate-limit backoff**; failures degrade silently to a git-log fallback. Org-scale mining of a big org will hit this.
2. **Org-scale mining is Python-only.** `mining/org_scale_scanner.py:1101` — `return []  # TODO: extend to Go interfaces, Java/TS`. Non-Python repos get empty results, silently.
3. **Calibration is schema, not practice.** The gate is enforced in code (≥100 holdout rows, ≥3 repos, Pearson ≥0.6) but the holdout *data* is explicitly partner-gated and out of scope — "deliberately out of scope for the codebase."
4. **The acceptance loop has certified the wrong thing, repeatedly.** Release evidence was produced by a `codeprobe` binary found on PATH (a 0.14.0rc2 uv tool, not the checkout being released — fixed in `faca987`); the evidence gate checked verdict *properties*, not *age* (0.14.0 nearly shipped on 0.13.0's verdicts — `4ffb5d8`); gate-skip inheritance silently skipped `publish` while reporting all-green (`f5e6095`); the real-agent gate is now **opt-in** (`ec0afb1`) — releases ship with no real-agent evidence unless two env vars + a credential secret are set. **Harden the provenance of the score before trusting the scorer.**
5. **Authors' own validity admissions** (`docs/conventions/validity-triage.md`): infra-crashed trials are stamped `automated_score=0.0`, and one incident dragged an arm's mean 0.72 → 0.645; the mitigation is a heuristic string-signal classifier. Oracle defects have burned them before (0%-valid answer keys, oracles pinned at the wrong commit — `fc0cd68`, `a9bdd7c`). Trust `mining/` outputs only with verification.
6. **Local experiment tree is NOT redacted at rest** (`docs/SNAPSHOT_REDACTION.md`): agent transcripts and `runs/trace.db` sit in cleartext; only token/auth patterns are redacted. Snapshot *export* defaults to hashes-only, but `.codeprobe/` artifacts are the exposure surface.
7. **Tenant isolation is advisory** (`tenant.py`/`tenant_lock.py`): `fcntl.flock` on a lockfile, stale-PID reclamation, no lock on Windows. Serializes same-user races; not a security boundary.
8. **Platform caveats:** `renameat2` called unconditionally (Linux-only) — macOS is "preview" for mining only. Runtime needs: Python 3.11–3.13, git, **Go toolchain** (AST scanner via `go run`), docker or podman, and the agent CLIs you want to test.
9. **`openai_compat` adapter is chat-completions only** — no tool use, no agent loop. Tau needs a real CLI adapter, not the API one.

## Architecture summary

File-based CLI eval pipeline + registry plugin model. `cli/` (presentation; `__init__.py` wires ~40 lazy commands) → `core/` (engine: executor, isolation, containment, checkpointing, scoring registries) → `analysis/` (stats + report + interpret). Extension contracts: `adapters/protocol.py` (AgentAdapter/AgentConfig/AgentOutput), `core/registry.py`, entry-points `codeprobe.agents` / `codeprobe.sessions` / `codeprobe.scorers`. Cross-cutting doctrines: **Zero-Fault-Counting** (app code does IO/parsing/arithmetic, never semantic judgment — enforced by a blocking lint), scorer-honesty lints, strict mypy + ruff, hermetic test suite (80% coverage gate).

## Health verdict: ADOPT (build on it) — with conditions

**Why adopt:** the most methodologically serious eval harness in this space — preregistered gates, multi-seed, harness-swap arms, fail-closed capabilities, honest cost accounting. The tau adapter seam is a clean extension point, not a fork-modification. Conventions are strict (mypy strict, ruff, hermetic tests) and the team fixes what breaks.

**Why conditionally:** god-objects everywhere (`cli/mine_cmd.py` 4489 lines with a 590-line 50-param `run_mine`; module-global mutable state as inter-invocation channel; `mining/writer.py` has **three module-level `main()` defs shadowing each other**; `core/executor.py:execute_task` 537 lines; `scorers.py:ArtifactScorer` carries three format generations as parallel methods; oracle scripts embedded as untypechecked string constants with a `normalize()` that must stay byte-identical across three copies). And the score-provenance chain (finding 4) has demonstrated false-confidence defects — treat its verdicts as claims to verify, not ground truth.

**Not recommended:** adopting its acceptance/release machinery uncritically, or running it uncontained (`--uncontained` executes mined verifier scripts outside the container behind a consent flag).

## First three concrete moves if adopted

1. **Unblock tau first, then write the adapter.** The engine must boot (missing `src/config/` — repair lane) before any adapter work. Then: one `TauAdapter` class implementing the `AgentAdapter` Protocol over tau's CLI, registered via entry-points, with brutally honest `AdapterCapabilities`. Half a day once the engine boots.
2. **Pilot on a foreign repo, not tau's own history.** Mine a small well-tested repo (e.g. `rich` or `isort` — the authors' own R0 corpus) and run a 2-arm experiment (tau vs claude) to validate the harness end-to-end: mining quality, verification contracts, cost accounting. Only then point it at tau's merged PRs.
3. **Harden score provenance for our runs.** Pin the codeprobe binary by content hash (never PATH-resolved), reject stale verdicts by age not just shape, keep experiment trees on encrypted storage (cleartext transcripts at rest), and re-verify a sample of mined tasks against their ground-truth commits before trusting a campaign.

---
*Skills used: blindspot-pass (domain unknowns), codemap (4 parallel mappers), code-quality-review (strict structural review). Zero Exa credits spent.*
