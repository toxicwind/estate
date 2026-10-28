# Workspace Markdown Audit Catalog

**Date:** 2026-09-20 (MDT) · **Scope:** every `.md` under `/home/hatch/workspace`, excluding only `mcpproxy-merge/`.

**Consolidation move:** the four loose `kimi-k3-*.md` research reports were moved to `audits/kimi-k3/` (destination-only cataloged).

Verdicts: `stale/superseded` | `keep-as-report` | `duplicate` | `actionable` — one-line verdict per file, based on the file's first ~40 lines. Exact content duplicates (SHA-256) are listed as pairwise pairs in the final section.

**File count:** 253 files cataloged (including this INDEX).

## root files

- `OPPORTUNITIES.md` — **keep-as-report** — OpenFang opportunity list; durable strategy notes, no action pending.
- `README-openfang-health.md` — **keep-as-report** — OpenFang/coyote liveness + provider audit reference for yote.
- `RECON.md` — **keep-as-report** — OpenFang/Coyote recon status snapshot 2026-09-20.
- `agent1-persona-PROPOSAL.md` — **actionable** — Proposal only, explicitly not deployed; decide or shelve.
- `canary-plan-kimi-auto-resolver.md` — **actionable** — Canary migration plan for kimi-auto-resolver; not yet executed.
- `code-racer-PAPERS.md` — **keep-as-report** — Completed paper research feeding the code-racer track.
- `github-muse-files-report.md` — **keep-as-report** — GitHub file search report for toxicwind; reference.
- `openfang-shingle-pilot-retirement.md` — **actionable** — Retirement runbook for shingle-pilot; execute or confirm done.
- `oracle-mechanism-spec.md` — **actionable** — Oracle-Market Mechanism Spec v1; implement the design.
- `resolve-2026-09-20-18.2.6.md` — **keep-as-report** — Delta-resolution report v18.1.18 → v18.2.6; completed.
- `rig-research-draft.md` — **actionable** — Research draft for Rig fork patches; continue into implementation.

## `audit-fix/`

- `audit-fix/exa-builder-report.md` — **keep-as-report** — Completed exa-builder report 2026-09-20.
- `audit-fix/ffs-verification-report.md` — **keep-as-report** — Completed FFS MCP tools live-verification report.
- `audit-fix/model-max-report.md` — **keep-as-report** — Completed MODEL-MAX integration + RPM audit report.
- `audit-fix/nemotron-vs-kimi-live.md` — **keep-as-report** — Completed live Nemotron-vs-Kimi herd audit.
- `audit-fix/pollinations-deep-dig.md` — **keep-as-report** — Completed Pollinations deep-dig report.
- `audit-fix/pollinations-ffs-report.md` — **keep-as-report** — Completed Pollinations + FFS report.
- `audit-fix/pollinations-security-notes.md` — **keep-as-report** — Completed Pollinations security-sweep notes.
- `audit-fix/race-port-report.md` — **keep-as-report** — Completed RACE-PORT (code racer as herd/race) report.
- `audit-fix/ranker-audit-report.md` — **keep-as-report** — Completed ranker audit report.
- `audit-fix/ranker-report.md` — **keep-as-report** — Completed provider-ranker bake-off report.
- `audit-fix/tau-config-report.md` — **keep-as-report** — Completed TAU-CONFIG overhaul report.
- `audit-fix/tau-herd-report.md` — **keep-as-report** — Completed tau-bin + herd audit/fix/optimize final report.

## `audits/`

- `audits/INDEX.md` — **keep-as-report** — This catalog — the master index of all workspace Markdown.

## `audits/kimi-k3/`

- `audits/kimi-k3/kimi-k3-herd-forensics.md` — **keep-as-report** — Completed Kimi K3-on-herd forensics; moved per consolidation.
- `audits/kimi-k3/kimi-k3-nim-community.md` — **keep-as-report** — Completed community-beliefs research on Kimi K3/NIM.
- `audits/kimi-k3/kimi-k3-nim-dig.md` — **keep-as-report** — Completed Kimi K3 NIM deep-dig.
- `audits/kimi-k3/kimi-k3-nim-wtf.md` — **keep-as-report** — Completed Kimi K3 NIM status brief.
- `audits/kimi-k3/kimi-k3-provider-research.md` — **keep-as-report** — Completed provider-pricing research (OpenRouter/Pollinations/NIM/Moonshot).

## `bid-market-build/`

- `bid-market-build/PROTOCOL.md` — **stale/superseded** — Superseded by bid-market-staging/WIRE.md (frozen v1).
- `bid-market-build/README.md` — **keep-as-report** — Design doc for the bidder agent; frozen reference.

## `bid-market-build/bidder/`

- `bid-market-build/bidder/README.md` — **keep-as-report** — Bidder-agent design doc; frozen reference.

## `bid-market-e2e/`

- `bid-market-e2e/E2E-REPORT.md` — **keep-as-report** — Completed bid-marketplace E2E report.
- `bid-market-e2e/README.md` — **keep-as-report** — E2E harness README; reference.

## `bid-market-staging/`

- `bid-market-staging/WIRE.md` — **keep-as-report** — Frozen wire-protocol v1 spec; canonical reference.
- `bid-market-staging/todos-entry.md` — **stale/superseded** — Done-log entry (T2-IMPL-AUCTIONEER shipped 2026-09-20 00:55 MDT).

## `canary/`

- `canary/runlog.md` — **keep-as-report** — Canary runlog for kimi-auto-resolver; historical record.

## `code-racer/`

- `code-racer/INTERFACE.md` — **keep-as-report** — Frozen harness interface contract v1; reference.
- `code-racer/README.md` — **keep-as-report** — Harness core README; reference.

## `code-racer-corpus/`

- `code-racer-corpus/E2E-REPORT-DRAFT.md` — **stale/superseded** — Draft superseded by code-racer-corpus/E2E-REPORT.md.
- `code-racer-corpus/E2E-REPORT.md` — **keep-as-report** — Completed code-racer E2E report.

## `code-racer-corpus/tasks/`

- `code-racer-corpus/tasks/CONTRACT.md` — **keep-as-report** — E2E addendum to the frozen harness contract; reference.
- `code-racer-corpus/tasks/README.md` — **keep-as-report** — Task corpus v2 README; reference.

## `code-racer-corpus/tasks/task-1-duration-parser/`

- `code-racer-corpus/tasks/task-1-duration-parser/PROBLEM.md` — **duplicate** — Exact duplicate of code-racer-corpus/tasks/task-1-duration-parser/task.md (sha256 61f209d06151).
- `code-racer-corpus/tasks/task-1-duration-parser/task.md` — **duplicate** — Exact duplicate of code-racer-corpus/tasks/task-1-duration-parser/PROBLEM.md (sha256 61f209d06151).

## `code-racer-corpus/tasks/task-2-bugfix-rate-limiter/`

- `code-racer-corpus/tasks/task-2-bugfix-rate-limiter/PROBLEM.md` — **duplicate** — Exact duplicate of code-racer-corpus/tasks/task-2-bugfix-rate-limiter/task.md (sha256 1340c9ed9d77).
- `code-racer-corpus/tasks/task-2-bugfix-rate-limiter/task.md` — **duplicate** — Exact duplicate of code-racer-corpus/tasks/task-2-bugfix-rate-limiter/PROBLEM.md (sha256 1340c9ed9d77).

## `code-racer-corpus/tasks/task-3-wordfreq-cli/`

- `code-racer-corpus/tasks/task-3-wordfreq-cli/PROBLEM.md` — **duplicate** — Exact duplicate of code-racer-corpus/tasks/task-3-wordfreq-cli/task.md (sha256 6e73ecac6d1d).
- `code-racer-corpus/tasks/task-3-wordfreq-cli/task.md` — **duplicate** — Exact duplicate of code-racer-corpus/tasks/task-3-wordfreq-cli/PROBLEM.md (sha256 6e73ecac6d1d).

## `code-racer-corpus/tasks/task-4-lru-cache/`

- `code-racer-corpus/tasks/task-4-lru-cache/PROBLEM.md` — **duplicate** — Exact duplicate of code-racer-corpus/tasks/task-4-lru-cache/task.md (sha256 9d2a948802e6).
- `code-racer-corpus/tasks/task-4-lru-cache/task.md` — **duplicate** — Exact duplicate of code-racer-corpus/tasks/task-4-lru-cache/PROBLEM.md (sha256 9d2a948802e6).

## `code-racer-strategies/`

- `code-racer-strategies/ADAPTER-INTERFACE.md` — **actionable** — Proposed adapter interface; review and adopt or reject.

## `code-racer/tasks/smoke-two-sum/`

- `code-racer/tasks/smoke-two-sum/task.md` — **keep-as-report** — Smoke task definition; harness fixture reference.

## `cron.d/daily/`

- `cron.d/daily/agentic-feature-tour__daily@10:52:00.md` — **keep-as-report** — Job descriptor for the daily feature tour; reference.

## `cron.d/minutely/`

- `cron.d/minutely/bridge-watchdog__interval@5m.md` — **keep-as-report** — Job descriptor for the 5m bridge watchdog; reference.
- `cron.d/minutely/heartbeat__interval@30m.md` — **keep-as-report** — Job descriptor for the 30m heartbeat; reference.
- `cron.d/minutely/kimi-auto-canary-judge__interval@5m.md` — **keep-as-report** — Job descriptor for the canary judge; reference.
- `cron.d/minutely/progress-watchdog__interval@3m.md` — **keep-as-report** — Job descriptor for the progress watchdog; reference.
- `cron.d/minutely/race-optimizer-watchdog__interval@5m.md` — **keep-as-report** — Job descriptor for the race-optimizer watchdog; reference.
- `cron.d/minutely/squawk-monitor__interval@5m.md` — **keep-as-report** — Job descriptor for the squawk monitor; reference.
- `cron.d/minutely/swarm-watchdog__interval@5m.md` — **keep-as-report** — Job descriptor for the swarm watchdog; reference.
- `cron.d/minutely/yote-connector-watch__interval@5m.md` — **keep-as-report** — Job descriptor for the yote-connector watch; reference.

## `debate-oracle-build/`

- `debate-oracle-build/INTERFACE.md` — **keep-as-report** — Oracle judge interface doc; reference.
- `debate-oracle-build/README-ORACLE.md` — **keep-as-report** — Oracle judge README; reference.

## `debate-oracle-build/prompts/`

- `debate-oracle-build/prompts/PROMPT-CHANGELOG.md` — **keep-as-report** — Prompt changelog; reference.
- `debate-oracle-build/prompts/oracle-v1.md` — **keep-as-report** — Oracle judge v1 prompt; reference.

## `docs/`

- `docs/README.md` — **keep-as-report** — Docs index; reference.
- `docs/personas.md` — **keep-as-report** — Ember/hatch vs Yote/coyote persona doc; reference.

## `docs/product/`

- `docs/product/README.md` — **keep-as-report** — Product surface doc; reference.
- `docs/product/app-ui.md` — **keep-as-report** — App UI driving doc; reference.

## `docs/product/widgets/`

- `docs/product/widgets/README.md` — **keep-as-report** — Widgets index; reference.
- `docs/product/widgets/widget-surfaces.md` — **keep-as-report** — Widget surfaces doc; reference.
- `docs/product/widgets/widgets-vs-artifacts.md` — **keep-as-report** — Widgets-vs-artifacts surface guide; reference.
- `docs/product/widgets/widgets.md` — **keep-as-report** — Widgets in-chat UI doc; reference.

## `docs/runtime/`

- `docs/runtime/README.md` — **keep-as-report** — Runtime explainer; reference.

## `e2e-tasks/`

- `e2e-tasks/E2E-REPORT.md` — **keep-as-report** — Completed debate-oracle E2E report.

## `emergent-tasking/market/`

- `emergent-tasking/market/task-bridge-recovery-runbook.md` — **actionable** — Open market task (URGENT): build the consolidated yote deploy runbook.
- `emergent-tasking/market/task-docs-audit-bridge-claims.md` — **actionable** — Open market task: audit documented bridge/herd/oracle claims vs evidence.
- `emergent-tasking/market/task-dryrun-herd-cleanup.md` — **actionable** — Open market task (high): dry-run review of the staged herd Kimi cleanup.
- `emergent-tasking/market/task-verify-oracle-build.md` — **actionable** — Open market task (high): adversarial verify of the staged oracle-market code.
- `emergent-tasking/market/task-yote-recovery-runbook.md` — **actionable** — Open market task: produce exact on-recovery command sequences.

## `emergent-tasking/squawk-queue/`

- `emergent-tasking/squawk-queue/1789895706-intro-oracle.md` — **actionable** — Queued oracle intro message; deliver via squawk on recovery.
- `emergent-tasking/squawk-queue/1789895706-task-open.md` — **actionable** — Queued task-open message; deliver via squawk on recovery.
- `emergent-tasking/squawk-queue/1789895716-intro-forge-forge.md` — **actionable** — Queued forge intro message; deliver via squawk on recovery.
- `emergent-tasking/squawk-queue/1789895717-intro-scout-scout.md` — **actionable** — Queued scout intro message; deliver via squawk on recovery.
- `emergent-tasking/squawk-queue/1789895735-win-scout.md` — **actionable** — Queued market-win message; deliver via squawk on recovery.
- `emergent-tasking/squawk-queue/1789895740-bid-forge.md` — **actionable** — Queued forge bid message; deliver via squawk on recovery.
- `emergent-tasking/squawk-queue/1789895750-intro-forge-forge.md` — **actionable** — Queued forge bidder intro message; deliver via squawk on recovery.
- `emergent-tasking/squawk-queue/1789895764-intro-scout-scout.md` — **actionable** — Queued scout bidder intro message; deliver via squawk on recovery.

## `feed/research/f63174fb-7e5f-4529-9367-9a51dc14e182/2026-09-19-evening-72406b26/`

- `feed/research/f63174fb-7e5f-4529-9367-9a51dc14e182/2026-09-19-evening-72406b26/web.md` — **keep-as-report** — Research web-capture snapshot; archive.

## `feed/research/f63174fb-7e5f-4529-9367-9a51dc14e182/2026-09-19-evening-dfc8b177/`

- `feed/research/f63174fb-7e5f-4529-9367-9a51dc14e182/2026-09-19-evening-dfc8b177/web.md` — **keep-as-report** — Research web-capture snapshot; archive.

## `flock-merge/`

- `flock-merge/BEHAVIOR-INVENTORY.md` — **keep-as-report** — Behavior inventory from code; merge reference.
- `flock-merge/INTEGRATION-RECONCILIATION.md` — **keep-as-report** — Canonical integration-reconciliation audit (priority 0).
- `flock-merge/MERGE-DESIGN.md` — **stale/superseded** — Superseded by flock-merge/INTEGRATION-RECONCILIATION.md.
- `flock-merge/MERGE-REPORT.md` — **keep-as-report** — Completed flock merge report.

## `goals/live-nemotron-vs-kimi-herd-audit/`

- `goals/live-nemotron-vs-kimi-herd-audit/GOAL.md` — **actionable** — Live audit goal still open; continue the audit.

## `goals/live-nemotron-vs-kimi-herd-audit/crons/minutely/`

- `goals/live-nemotron-vs-kimi-herd-audit/crons/minutely/audit-bridge-watch__interval@5m.md` — **keep-as-report** — Job descriptor for the audit bridge watch; reference.

## `hatch-maximal/`

- `hatch-maximal/MEASURE.md` — **keep-as-report** — Completed cell-measurement + offender audit.
- `hatch-maximal/PAPERS.md` — **keep-as-report** — Completed paper research on 2-vCPU throughput.
- `hatch-maximal/REMEASURE.md` — **keep-as-report** — Completed remeasure after the event-driven rewrite.
- `hatch-maximal/REPOS.md` — **keep-as-report** — Completed GitHub-retrieval log for the rewrite.

## `hatch-maximal/vendor/incr/`

- `hatch-maximal/vendor/incr/CHANGELOG.md` — **keep-as-report** — Third-party changelog; vendored reference.
- `hatch-maximal/vendor/incr/README.md` — **keep-as-report** — Third-party README; vendored reference.

## `hatch-maximal/vendor/incr/crates/incr-compute/`

- `hatch-maximal/vendor/incr/crates/incr-compute/README.md` — **keep-as-report** — Third-party crate README; vendored reference.

## `hatch-maximal/vendor/incr/crates/incr-concurrent/`

- `hatch-maximal/vendor/incr/crates/incr-concurrent/README.md` — **keep-as-report** — Third-party crate README; vendored reference.

## `hatch-maximal/vendor/incr/crates/incr-core/`

- `hatch-maximal/vendor/incr/crates/incr-core/README.md` — **keep-as-report** — Third-party crate README; vendored reference.

## `hatch-maximal/vendor/incr/crates/incr-kube/`

- `hatch-maximal/vendor/incr/crates/incr-kube/README.md` — **keep-as-report** — Third-party crate README; vendored reference.

## `hatch-maximal/vendor/kinesin/`

- `hatch-maximal/vendor/kinesin/README.md` — **keep-as-report** — Third-party README; vendored reference.
- `hatch-maximal/vendor/kinesin/TODO.md` — **keep-as-report** — Third-party TODO; vendored reference.

## `hatch-maximal/vendor/watchdog/`

- `hatch-maximal/vendor/watchdog/THIRD_PARTY_LICENSES.md` — **keep-as-report** — Third-party license bundle; vendored reference.

## `hatch-maximal/vendor/watchdog/docs/source/`

- `hatch-maximal/vendor/watchdog/docs/source/contributors.md` — **keep-as-report** — Third-party contributors doc; vendored reference.

## `hatch-maximal/vendor/watchfiles/`

- `hatch-maximal/vendor/watchfiles/README.md` — **keep-as-report** — Third-party README; vendored reference.

## `hatch-maximal/vendor/watchfiles/docs/`

- `hatch-maximal/vendor/watchfiles/docs/cli.md` — **keep-as-report** — Third-party docs; vendored reference.
- `hatch-maximal/vendor/watchfiles/docs/index.md` — **keep-as-report** — Third-party docs; vendored reference.
- `hatch-maximal/vendor/watchfiles/docs/migrating.md` — **keep-as-report** — Third-party docs; vendored reference.

## `hatch-maximal/vendor/watchfiles/docs/api/`

- `hatch-maximal/vendor/watchfiles/docs/api/filters.md` — **keep-as-report** — Third-party API docs; vendored reference.
- `hatch-maximal/vendor/watchfiles/docs/api/run_process.md` — **keep-as-report** — Third-party API docs; vendored reference.
- `hatch-maximal/vendor/watchfiles/docs/api/rust_backend.md` — **keep-as-report** — Third-party API docs; vendored reference.
- `hatch-maximal/vendor/watchfiles/docs/api/watch.md` — **keep-as-report** — Third-party API docs; vendored reference.

## `hatch-maximal/vendor/watchfiles/tests/test_files/`

- `hatch-maximal/vendor/watchfiles/tests/test_files/README.md` — **keep-as-report** — Third-party test fixture README; vendored reference.

## `hatch-maximal/vendor/yyds-fswatch/`

- `hatch-maximal/vendor/yyds-fswatch/CHANGELOG.md` — **keep-as-report** — Third-party changelog; vendored reference.
- `hatch-maximal/vendor/yyds-fswatch/README.md` — **keep-as-report** — Third-party README; vendored reference.
- `hatch-maximal/vendor/yyds-fswatch/README_CN.md` — **keep-as-report** — Third-party README (CN); vendored reference.

## `herd-kimi-cleanup/`

- `herd-kimi-cleanup/README.md` — **actionable** — Staged cleanup plan; NOT applied — run on yote once the bridge recovers.

## `model-max/`

- `model-max/README.md` — **keep-as-report** — MODEL-MAX herd model measurement doc; reference.

## `nim-probes/`

- `nim-probes/NIM-PROBE-REPORT.md` — **keep-as-report** — Completed NIM live-probe report 2026-09-20.

## `nvidia-alive/`

- `nvidia-alive/README.md` — **keep-as-report** — nvidia-alive tracker README; reference.

## `nvidia-alive/alive/`

- `nvidia-alive/alive/README.md` — **keep-as-report** — Endpoint-alive model-list README; reference.

## `nvidia-alive/docs/`

- `nvidia-alive/docs/ENDPOINT-AUDIT-PLAN.md` — **actionable** — Endpoint-only audit plan; execute the plan.
- `nvidia-alive/docs/FINDINGS.md` — **keep-as-report** — Completed solved-findings log.
- `nvidia-alive/docs/KIMI-K3-NIM.md` — **keep-as-report** — Completed Kimi-K3/NIM investigation, debate, and plan.
- `nvidia-alive/docs/kimi-k3-debate-kimi-card.md` — **keep-as-report** — Completed debate position (pro-thesis).
- `nvidia-alive/docs/kimi-k3-defense.md` — **keep-as-report** — Completed kimi-defender brief (kimi-k3 ALIVE on NIM).

## `oracle-build/`

- `oracle-build/RESUME.md` — **actionable** — On-recovery resume checklist for the oracle-market replay fix; run when the bridge recovers.

## `paper-research/`

- `paper-research/related-papers.md` — **keep-as-report** — Related-papers list; reference.

## `reorg-plan/`

- `reorg-plan/REORG-PLAN.md` — **actionable** — Sovereign reorg plan (shingle → hatch/agents/ember); approve or execute.

## `reorg-work/`

- `reorg-work/REORG-PLAN.md` — **actionable** — Working copy of the sovereign reorg plan; approve or execute.

## `router/`

- `router/README.md` — **keep-as-report** — Cross-box router README; reference.
- `router/hatch_send-v2-spec.md` — **actionable** — hatch_send v2 spec; implement the execution channel.
- `router/yote_send.patch.md` — **actionable** — Staged MCP tool patch for yote's awrawr_mcp.py; apply on yote.

## `router-patches/`

- `router-patches/ROUTER.md` — **keep-as-report** — Sovereign Router v3.2 doc; reference.

## `self_improvement/objectives/goals_bookkeeping/`

- `self_improvement/objectives/goals_bookkeeping/CURRENT.md` — **stale/superseded** — Generated snapshot; superseded by newer archive snapshots.

## `self_improvement/objectives/goals_bookkeeping/archive/`

- `self_improvement/objectives/goals_bookkeeping/archive/20260919T130055Z.CURRENT.md` — **stale/superseded** — Historical generated snapshot; archive.
- `self_improvement/objectives/goals_bookkeeping/archive/20260919T185813Z.CURRENT.md` — **stale/superseded** — Historical generated snapshot; archive.
- `self_improvement/objectives/goals_bookkeeping/archive/20260920T005812Z.CURRENT.md` — **stale/superseded** — Historical generated snapshot; archive.

## `self_improvement/objectives/memory/`

- `self_improvement/objectives/memory/CURRENT.md` — **stale/superseded** — Generated snapshot; superseded by newer archive snapshots.

## `self_improvement/objectives/memory/archive/`

- `self_improvement/objectives/memory/archive/20260920T040301Z.CURRENT.md` — **stale/superseded** — Historical generated snapshot; archive.
- `self_improvement/objectives/memory/archive/20260920T064126Z.CURRENT.md` — **stale/superseded** — Historical generated snapshot; archive.

## `self_improvement/objectives/proactive_notifier/`

- `self_improvement/objectives/proactive_notifier/CURRENT.md` — **stale/superseded** — Generated snapshot; archive.

## `self_improvement/objectives/relationships/`

- `self_improvement/objectives/relationships/CURRENT.md` — **stale/superseded** — Generated snapshot; superseded by newer archive snapshots.

## `self_improvement/objectives/relationships/archive/`

- `self_improvement/objectives/relationships/archive/20260920T042533Z.CURRENT.md` — **stale/superseded** — Historical generated snapshot; archive.
- `self_improvement/objectives/relationships/archive/20260920T052552Z.CURRENT.md` — **stale/superseded** — Historical generated snapshot; archive.
- `self_improvement/objectives/relationships/archive/20260920T062648Z.CURRENT.md` — **stale/superseded** — Historical generated snapshot; archive.

## `self_improvement/objectives/shopping/`

- `self_improvement/objectives/shopping/CURRENT.md` — **stale/superseded** — Generated snapshot; archive.

## `self_improvement/objectives/urgency_classifier/`

- `self_improvement/objectives/urgency_classifier/CURRENT.md` — **stale/superseded** — Generated snapshot; superseded by newer archive snapshots.

## `self_improvement/objectives/urgency_classifier/archive/`

- `self_improvement/objectives/urgency_classifier/archive/20260920T080109Z.CURRENT.md` — **stale/superseded** — Historical generated snapshot; archive.
- `self_improvement/objectives/urgency_classifier/archive/20260920T080122Z.CURRENT.md` — **stale/superseded** — Historical generated snapshot; archive.
- `self_improvement/objectives/urgency_classifier/archive/20260920T080213Z.CURRENT.md` — **stale/superseded** — Historical generated snapshot; archive.
- `self_improvement/objectives/urgency_classifier/archive/20260920T080317Z.CURRENT.md` — **stale/superseded** — Historical generated snapshot; archive.
- `self_improvement/objectives/urgency_classifier/archive/20260920T081943Z.CURRENT.md` — **stale/superseded** — Historical generated snapshot; archive.
- `self_improvement/objectives/urgency_classifier/archive/20260920T082725Z.CURRENT.md` — **stale/superseded** — Historical generated snapshot; archive.
- `self_improvement/objectives/urgency_classifier/archive/20260920T083908Z.CURRENT.md` — **stale/superseded** — Historical generated snapshot; archive.
- `self_improvement/objectives/urgency_classifier/archive/20260920T083956Z.CURRENT.md` — **stale/superseded** — Historical generated snapshot; archive.
- `self_improvement/objectives/urgency_classifier/archive/20260920T084024Z.CURRENT.md` — **stale/superseded** — Historical generated snapshot; archive.
- `self_improvement/objectives/urgency_classifier/archive/20260920T084053Z.CURRENT.md` — **stale/superseded** — Historical generated snapshot; archive.
- `self_improvement/objectives/urgency_classifier/archive/20260920T084132Z.CURRENT.md` — **stale/superseded** — Historical generated snapshot; archive.
- `self_improvement/objectives/urgency_classifier/archive/20260920T084207Z.CURRENT.md` — **stale/superseded** — Historical generated snapshot; archive.
- `self_improvement/objectives/urgency_classifier/archive/20260920T084330Z.CURRENT.md` — **stale/superseded** — Historical generated snapshot; archive.
- `self_improvement/objectives/urgency_classifier/archive/20260920T084401Z.CURRENT.md` — **stale/superseded** — Historical generated snapshot; archive.
- `self_improvement/objectives/urgency_classifier/archive/20260920T084501Z.CURRENT.md` — **stale/superseded** — Historical generated snapshot; archive.
- `self_improvement/objectives/urgency_classifier/archive/20260920T085110Z.CURRENT.md` — **stale/superseded** — Historical generated snapshot; archive.
- `self_improvement/objectives/urgency_classifier/archive/20260920T085140Z.CURRENT.md` — **stale/superseded** — Historical generated snapshot; archive.
- `self_improvement/objectives/urgency_classifier/archive/20260920T085242Z.CURRENT.md` — **stale/superseded** — Historical generated snapshot; archive.
- `self_improvement/objectives/urgency_classifier/archive/20260920T085545Z.CURRENT.md` — **stale/superseded** — Historical generated snapshot; archive.
- `self_improvement/objectives/urgency_classifier/archive/20260920T090108Z.CURRENT.md` — **stale/superseded** — Historical generated snapshot; archive.

## `self_improvement/staging/memory/sirun_07690a9645aa41fe8595d48b9a8695c9/memory_reconciliation/pinned/`

- `self_improvement/staging/memory/sirun_07690a9645aa41fe8595d48b9a8695c9/memory_reconciliation/pinned/MEMORY.numbered.md` — **duplicate** — Exact duplicate of self_improvement/staging/memory/sirun_50ff259ef8814004845d544874e523ce/memory_reconciliation/pinned/MEMORY.numbered.md (sha256 abad72609044).
- `self_improvement/staging/memory/sirun_07690a9645aa41fe8595d48b9a8695c9/memory_reconciliation/pinned/MEMORY.pinned.md` — **duplicate** — Exact duplicate of 3 reconciliation snapshots (sha256 f699b4a6f53d): pinned/MEMORY.pinned.md + review/MEMORY.before.md for sirun_07690a9645aa41fe8595d48b9a8695c9 and sirun_50ff259ef8814004845d544874e523ce.

## `self_improvement/staging/memory/sirun_07690a9645aa41fe8595d48b9a8695c9/memory_reconciliation/review/`

- `self_improvement/staging/memory/sirun_07690a9645aa41fe8595d48b9a8695c9/memory_reconciliation/review/MEMORY.before.md` — **duplicate** — Exact duplicate of 3 reconciliation snapshots (sha256 f699b4a6f53d): pinned/MEMORY.pinned.md + review/MEMORY.before.md for sirun_07690a9645aa41fe8595d48b9a8695c9 and sirun_50ff259ef8814004845d544874e523ce.
- `self_improvement/staging/memory/sirun_07690a9645aa41fe8595d48b9a8695c9/memory_reconciliation/review/MEMORY.md` — **stale/superseded** — Staging reconciliation artifact; historical.

## `self_improvement/staging/memory/sirun_34a6b02939eb493f884ad7752317db48/memory_reconciliation/pinned/`

- `self_improvement/staging/memory/sirun_34a6b02939eb493f884ad7752317db48/memory_reconciliation/pinned/MEMORY.numbered.md` — **stale/superseded** — Staging reconciliation artifact; historical.
- `self_improvement/staging/memory/sirun_34a6b02939eb493f884ad7752317db48/memory_reconciliation/pinned/MEMORY.pinned.md` — **duplicate** — Exact duplicate of self_improvement/staging/memory/sirun_34a6b02939eb493f884ad7752317db48/memory_reconciliation/review/MEMORY.before.md (sha256 ce2e3a048890).

## `self_improvement/staging/memory/sirun_34a6b02939eb493f884ad7752317db48/memory_reconciliation/review/`

- `self_improvement/staging/memory/sirun_34a6b02939eb493f884ad7752317db48/memory_reconciliation/review/MEMORY.before.md` — **duplicate** — Exact duplicate of self_improvement/staging/memory/sirun_34a6b02939eb493f884ad7752317db48/memory_reconciliation/pinned/MEMORY.pinned.md (sha256 ce2e3a048890).
- `self_improvement/staging/memory/sirun_34a6b02939eb493f884ad7752317db48/memory_reconciliation/review/MEMORY.md` — **stale/superseded** — Staging reconciliation artifact; historical.

## `self_improvement/staging/memory/sirun_50ff259ef8814004845d544874e523ce/memory_reconciliation/pinned/`

- `self_improvement/staging/memory/sirun_50ff259ef8814004845d544874e523ce/memory_reconciliation/pinned/MEMORY.numbered.md` — **duplicate** — Exact duplicate of self_improvement/staging/memory/sirun_07690a9645aa41fe8595d48b9a8695c9/memory_reconciliation/pinned/MEMORY.numbered.md (sha256 abad72609044).
- `self_improvement/staging/memory/sirun_50ff259ef8814004845d544874e523ce/memory_reconciliation/pinned/MEMORY.pinned.md` — **duplicate** — Exact duplicate of 3 reconciliation snapshots (sha256 f699b4a6f53d): pinned/MEMORY.pinned.md + review/MEMORY.before.md for sirun_07690a9645aa41fe8595d48b9a8695c9 and sirun_50ff259ef8814004845d544874e523ce.

## `self_improvement/staging/memory/sirun_50ff259ef8814004845d544874e523ce/memory_reconciliation/review/`

- `self_improvement/staging/memory/sirun_50ff259ef8814004845d544874e523ce/memory_reconciliation/review/MEMORY.before.md` — **duplicate** — Exact duplicate of 3 reconciliation snapshots (sha256 f699b4a6f53d): pinned/MEMORY.pinned.md + review/MEMORY.before.md for sirun_07690a9645aa41fe8595d48b9a8695c9 and sirun_50ff259ef8814004845d544874e523ce.
- `self_improvement/staging/memory/sirun_50ff259ef8814004845d544874e523ce/memory_reconciliation/review/MEMORY.md` — **stale/superseded** — Staging reconciliation artifact; historical.

## `self_improvement/staging/memory/sirun_7fb8a4b094a141079888fa442047899f/memory_reconciliation/pinned/`

- `self_improvement/staging/memory/sirun_7fb8a4b094a141079888fa442047899f/memory_reconciliation/pinned/MEMORY.numbered.md` — **stale/superseded** — Staging reconciliation artifact; historical.
- `self_improvement/staging/memory/sirun_7fb8a4b094a141079888fa442047899f/memory_reconciliation/pinned/MEMORY.pinned.md` — **stale/superseded** — Staging reconciliation artifact; historical.

## `self_improvement/staging/memory/sirun_a06f16e7ccd1493ea040e0c7e263d026/memory_reconciliation/pinned/`

- `self_improvement/staging/memory/sirun_a06f16e7ccd1493ea040e0c7e263d026/memory_reconciliation/pinned/MEMORY.numbered.md` — **stale/superseded** — Staging reconciliation artifact; historical.
- `self_improvement/staging/memory/sirun_a06f16e7ccd1493ea040e0c7e263d026/memory_reconciliation/pinned/MEMORY.pinned.md` — **stale/superseded** — Staging reconciliation artifact; historical.

## `self_improvement/staging/memory/sirun_b9d67a35fc9a4d8c817d1b98cc3b5f8a/memory_reconciliation/pinned/`

- `self_improvement/staging/memory/sirun_b9d67a35fc9a4d8c817d1b98cc3b5f8a/memory_reconciliation/pinned/MEMORY.numbered.md` — **stale/superseded** — Staging reconciliation artifact; historical.
- `self_improvement/staging/memory/sirun_b9d67a35fc9a4d8c817d1b98cc3b5f8a/memory_reconciliation/pinned/MEMORY.pinned.md` — **stale/superseded** — Staging reconciliation artifact; historical.

## `self_improvement/staging/memory/sirun_c6f3d39598fa4ef89f3f516f5539488c/memory_reconciliation/pinned/`

- `self_improvement/staging/memory/sirun_c6f3d39598fa4ef89f3f516f5539488c/memory_reconciliation/pinned/MEMORY.numbered.md` — **stale/superseded** — Staging reconciliation artifact; historical.
- `self_improvement/staging/memory/sirun_c6f3d39598fa4ef89f3f516f5539488c/memory_reconciliation/pinned/MEMORY.pinned.md` — **stale/superseded** — Staging reconciliation artifact; historical.

## `skills/agent-audit/`

- `skills/agent-audit/SKILL.md` — **keep-as-report** — Skill definition doc; reference.

## `skills/emergent-tasking/`

- `skills/emergent-tasking/SKILL.md` — **keep-as-report** — Skill definition doc; reference.

## `skills/emergent-tasking/references/`

- `skills/emergent-tasking/references/roles-and-ledger.md` — **keep-as-report** — Reference doc; reference.

## `skills/exa/`

- `skills/exa/SKILL.md` — **keep-as-report** — Skill definition doc; reference.

## `skills/github/`

- `skills/github/SKILL.md` — **keep-as-report** — Skill definition doc; reference.

## `skills/github-mcp/`

- `skills/github-mcp/SKILL.md` — **keep-as-report** — Skill definition doc; reference.

## `skills/race/`

- `skills/race/SKILL.md` — **keep-as-report** — Skill definition doc; reference.

## `skills/router/`

- `skills/router/SKILL.md` — **keep-as-report** — Skill definition doc; reference.

## `squawk/`

- `squawk/RACE-PROTOCOL.md` — **keep-as-report** — Race protocol v1; reference.

## `squawk-relay-staging/`

- `squawk-relay-staging/PAPERS.md` — **keep-as-report** — Completed relay paper research.
- `squawk-relay-staging/README.md` — **keep-as-report** — Durable outbox relay README; reference.
- `squawk-relay-staging/openfang-spawn.md` — **actionable** — Agent instantiation doc, READY TO EXECUTE; blocked on daemon LLM path.

## `tau-bin-audit/`

- `tau-bin-audit/archive-README.md` — **keep-as-report** — Non-destructive archive README; reference.

## `tau-merge/`

- `tau-merge/README.md` — **keep-as-report** — Upstream-merge system README; reference.

## `toolcall-agent-src/`

- `toolcall-agent-src/OPPORTUNITIES.md` — **keep-as-report** — Toolcall-agent opportunities running list; reference.

## `transfer/shakedown/`

- `transfer/shakedown/README-debate.md` — **keep-as-report** — Debate-oracle operator README; reference.

## `venvs/guidellm/lib/python3.12/site-packages/cuda/pathfinder/`

- `venvs/guidellm/lib/python3.12/site-packages/cuda/pathfinder/README.md` — **keep-as-report** — Third-party doc stub; vendored reference.

## `venvs/guidellm/lib/python3.12/site-packages/httpcore-1.0.9.dist-info/licenses/`

- `venvs/guidellm/lib/python3.12/site-packages/httpcore-1.0.9.dist-info/licenses/LICENSE.md` — **keep-as-report** — Third-party license; vendored reference.

## `venvs/guidellm/lib/python3.12/site-packages/httpx-0.28.1.dist-info/licenses/`

- `venvs/guidellm/lib/python3.12/site-packages/httpx-0.28.1.dist-info/licenses/LICENSE.md` — **keep-as-report** — Third-party license; vendored reference.

## `venvs/guidellm/lib/python3.12/site-packages/huggingface_hub/templates/`

- `venvs/guidellm/lib/python3.12/site-packages/huggingface_hub/templates/datasetcard_template.md` — **keep-as-report** — Third-party template; vendored reference.
- `venvs/guidellm/lib/python3.12/site-packages/huggingface_hub/templates/modelcard_template.md` — **keep-as-report** — Third-party template; vendored reference.

## `venvs/guidellm/lib/python3.12/site-packages/idna-3.20.dist-info/licenses/`

- `venvs/guidellm/lib/python3.12/site-packages/idna-3.20.dist-info/licenses/LICENSE.md` — **keep-as-report** — Third-party license; vendored reference.

## `venvs/guidellm/lib/python3.12/site-packages/numpy-2.5.3.dist-info/licenses/numpy/_core/src/npysort/x86-simd-sort/`

- `venvs/guidellm/lib/python3.12/site-packages/numpy-2.5.3.dist-info/licenses/numpy/_core/src/npysort/x86-simd-sort/LICENSE.md` — **keep-as-report** — Third-party license; vendored reference.

## `venvs/guidellm/lib/python3.12/site-packages/numpy-2.5.3.dist-info/licenses/numpy/fft/pocketfft/`

- `venvs/guidellm/lib/python3.12/site-packages/numpy-2.5.3.dist-info/licenses/numpy/fft/pocketfft/LICENSE.md` — **keep-as-report** — Third-party license; vendored reference.

## `venvs/guidellm/lib/python3.12/site-packages/numpy-2.5.3.dist-info/licenses/numpy/random/`

- `venvs/guidellm/lib/python3.12/site-packages/numpy-2.5.3.dist-info/licenses/numpy/random/LICENSE.md` — **duplicate** — Exact duplicate of venvs/guidellm/lib/python3.12/site-packages/numpy/random/LICENSE.md (sha256 103166b62b80).

## `venvs/guidellm/lib/python3.12/site-packages/numpy-2.5.3.dist-info/licenses/numpy/random/src/distributions/`

- `venvs/guidellm/lib/python3.12/site-packages/numpy-2.5.3.dist-info/licenses/numpy/random/src/distributions/LICENSE.md` — **keep-as-report** — Third-party license; vendored reference.

## `venvs/guidellm/lib/python3.12/site-packages/numpy-2.5.3.dist-info/licenses/numpy/random/src/mt19937/`

- `venvs/guidellm/lib/python3.12/site-packages/numpy-2.5.3.dist-info/licenses/numpy/random/src/mt19937/LICENSE.md` — **keep-as-report** — Third-party license; vendored reference.

## `venvs/guidellm/lib/python3.12/site-packages/numpy-2.5.3.dist-info/licenses/numpy/random/src/pcg64/`

- `venvs/guidellm/lib/python3.12/site-packages/numpy-2.5.3.dist-info/licenses/numpy/random/src/pcg64/LICENSE.md` — **keep-as-report** — Third-party license; vendored reference.

## `venvs/guidellm/lib/python3.12/site-packages/numpy-2.5.3.dist-info/licenses/numpy/random/src/philox/`

- `venvs/guidellm/lib/python3.12/site-packages/numpy-2.5.3.dist-info/licenses/numpy/random/src/philox/LICENSE.md` — **keep-as-report** — Third-party license; vendored reference.

## `venvs/guidellm/lib/python3.12/site-packages/numpy-2.5.3.dist-info/licenses/numpy/random/src/sfc64/`

- `venvs/guidellm/lib/python3.12/site-packages/numpy-2.5.3.dist-info/licenses/numpy/random/src/sfc64/LICENSE.md` — **keep-as-report** — Third-party license; vendored reference.

## `venvs/guidellm/lib/python3.12/site-packages/numpy-2.5.3.dist-info/licenses/numpy/random/src/splitmix64/`

- `venvs/guidellm/lib/python3.12/site-packages/numpy-2.5.3.dist-info/licenses/numpy/random/src/splitmix64/LICENSE.md` — **keep-as-report** — Third-party license; vendored reference.

## `venvs/guidellm/lib/python3.12/site-packages/numpy/random/`

- `venvs/guidellm/lib/python3.12/site-packages/numpy/random/LICENSE.md` — **duplicate** — Exact duplicate of venvs/guidellm/lib/python3.12/site-packages/numpy-2.5.3.dist-info/licenses/numpy/random/LICENSE.md (sha256 103166b62b80).

## `venvs/guidellm/lib/python3.12/site-packages/pyarrow/tests/data/orc/`

- `venvs/guidellm/lib/python3.12/site-packages/pyarrow/tests/data/orc/README.md` — **keep-as-report** — Third-party test-data README; vendored reference.

## `venvs/guidellm/lib/python3.12/site-packages/triton/experimental/gsan/`

- `venvs/guidellm/lib/python3.12/site-packages/triton/experimental/gsan/README.md` — **keep-as-report** — Third-party design proposal; vendored reference.

## `venvs/guidellm/lib/python3.12/site-packages/typer/.agents/skills/typer/`

- `venvs/guidellm/lib/python3.12/site-packages/typer/.agents/skills/typer/SKILL.md` — **keep-as-report** — Third-party skill doc; vendored reference.

## `yote-consolidation/`

- `yote-consolidation/OWNERSHIP.md` — **keep-as-report** — Mesh ownership map; completed consolidation reference.
- `yote-consolidation/PLAN.md` — **keep-as-report** — Completed consolidation plan (2026-09-20); historical.
- `yote-consolidation/kimi-k3-nim-truth.md` — **keep-as-report** — Completed Kimi K3 NIM truth brief.
- `yote-consolidation/ralph-inventory.md` — **keep-as-report** — Completed Ralph code inventory.
- `yote-consolidation/server-bytecode-debug.md` — **keep-as-report** — Completed bridge-server bytecode debug report.
- `yote-consolidation/web-ui-inventory.md` — **keep-as-report** — Completed Web UI fleet inventory.

## `yote-consolidation/deploy-review/`

- `yote-consolidation/deploy-review/VERIFY.md` — **actionable** — Post-apply verification checklist; run after any deploy apply.

## `yote-consolidation/inventory/`

- `yote-consolidation/inventory/code-hits.md` — **keep-as-report** — Completed GitHub code-search inventory (635 hits).
- `yote-consolidation/inventory/repos.md` — **keep-as-report** — Completed GitHub repo inventory (473 repos).

## `yote-consolidation/manifest/`

- `yote-consolidation/manifest/merge-a-rust.md` — **keep-as-report** — Completed Rust-gateway merge manifest.
- `yote-consolidation/manifest/merge-b-bridge.md` — **keep-as-report** — Completed bridge-copy merge manifest.
- `yote-consolidation/manifest/merge-b-ops.md` — **keep-as-report** — Completed gist→ops migration manifest.
- `yote-consolidation/manifest/merge-b-sync.md` — **keep-as-report** — Completed vendored ws_daemon.py sync manifest.
- `yote-consolidation/manifest/merge-c-diff.md` — **keep-as-report** — Completed stale-mirror diff report.
- `yote-consolidation/manifest/merge-d-deploy.md` — **keep-as-report** — Completed deploy-bundle manifest.
- `yote-consolidation/manifest/merge-e-repoint.md` — **keep-as-report** — Completed gist-repoint/deprecation manifest.

## `yote-consolidation/staging/`

- `yote-consolidation/staging/CONSOLIDATION.md` — **keep-as-report** — Completed consolidation manifest; historical.
- `yote-consolidation/staging/README.md` — **keep-as-report** — Consolidated project index; reference.
- `yote-consolidation/staging/README.merged.md` — **keep-as-report** — Staging copy of the consolidated README; reference.

## `yote-maximal/`

- `yote-maximal/TUNING-PLAN.md` — **actionable** — Herd throughput tuning plan; staged, awaiting bridge recovery.

## `yote-ops/`

- `yote-ops/anthropic-flock-fix-plan.md` — **actionable** — Repair plan staged; run once the bridge is back.
- `yote-ops/anthropic-flock-fleet-post.md` — **actionable** — Draft fleet post; send via squawk once the bridge is back.

## `your_files/`

- `your_files/tau-kdl-rot-report-2026-09-19.md` — **keep-as-report** — Completed Tau KDL rot report 2026-09-19.

## Duplicate pairs (exact content, SHA-256)

- `code-racer-corpus/tasks/task-1-duration-parser/PROBLEM.md` ↔ `code-racer-corpus/tasks/task-1-duration-parser/task.md` — sha256 `61f209d06151`
- `code-racer-corpus/tasks/task-2-bugfix-rate-limiter/PROBLEM.md` ↔ `code-racer-corpus/tasks/task-2-bugfix-rate-limiter/task.md` — sha256 `1340c9ed9d77`
- `code-racer-corpus/tasks/task-3-wordfreq-cli/PROBLEM.md` ↔ `code-racer-corpus/tasks/task-3-wordfreq-cli/task.md` — sha256 `6e73ecac6d1d`
- `code-racer-corpus/tasks/task-4-lru-cache/PROBLEM.md` ↔ `code-racer-corpus/tasks/task-4-lru-cache/task.md` — sha256 `9d2a948802e6`
- `venvs/guidellm/lib/python3.12/site-packages/numpy/random/LICENSE.md` ↔ `venvs/guidellm/lib/python3.12/site-packages/numpy-2.5.3.dist-info/licenses/numpy/random/LICENSE.md` — sha256 `103166b62b80`
- `self_improvement/staging/memory/sirun_07690a9645aa41fe8595d48b9a8695c9/memory_reconciliation/pinned/MEMORY.numbered.md` ↔ `self_improvement/staging/memory/sirun_50ff259ef8814004845d544874e523ce/memory_reconciliation/pinned/MEMORY.numbered.md` — sha256 `abad72609044`
- `self_improvement/staging/memory/sirun_34a6b02939eb493f884ad7752317db48/memory_reconciliation/pinned/MEMORY.pinned.md` ↔ `self_improvement/staging/memory/sirun_34a6b02939eb493f884ad7752317db48/memory_reconciliation/review/MEMORY.before.md` — sha256 `ce2e3a048890`
- `self_improvement/staging/memory/sirun_07690a9645aa41fe8595d48b9a8695c9/memory_reconciliation/pinned/MEMORY.pinned.md` ↔ `self_improvement/staging/memory/sirun_07690a9645aa41fe8595d48b9a8695c9/memory_reconciliation/review/MEMORY.before.md` — sha256 `f699b4a6f53d`
- `self_improvement/staging/memory/sirun_07690a9645aa41fe8595d48b9a8695c9/memory_reconciliation/pinned/MEMORY.pinned.md` ↔ `self_improvement/staging/memory/sirun_50ff259ef8814004845d544874e523ce/memory_reconciliation/pinned/MEMORY.pinned.md` — sha256 `f699b4a6f53d`
- `self_improvement/staging/memory/sirun_07690a9645aa41fe8595d48b9a8695c9/memory_reconciliation/pinned/MEMORY.pinned.md` ↔ `self_improvement/staging/memory/sirun_50ff259ef8814004845d544874e523ce/memory_reconciliation/review/MEMORY.before.md` — sha256 `f699b4a6f53d`
- `self_improvement/staging/memory/sirun_07690a9645aa41fe8595d48b9a8695c9/memory_reconciliation/review/MEMORY.before.md` ↔ `self_improvement/staging/memory/sirun_50ff259ef8814004845d544874e523ce/memory_reconciliation/pinned/MEMORY.pinned.md` — sha256 `f699b4a6f53d`
- `self_improvement/staging/memory/sirun_07690a9645aa41fe8595d48b9a8695c9/memory_reconciliation/review/MEMORY.before.md` ↔ `self_improvement/staging/memory/sirun_50ff259ef8814004845d544874e523ce/memory_reconciliation/review/MEMORY.before.md` — sha256 `f699b4a6f53d`
- `self_improvement/staging/memory/sirun_50ff259ef8814004845d544874e523ce/memory_reconciliation/pinned/MEMORY.pinned.md` ↔ `self_improvement/staging/memory/sirun_50ff259ef8814004845d544874e523ce/memory_reconciliation/review/MEMORY.before.md` — sha256 `f699b4a6f53d`

SHA-256 recomputed across every cataloged file immediately before writing this catalog; the 7 duplicate groups above produce exactly these 13 pairs.
