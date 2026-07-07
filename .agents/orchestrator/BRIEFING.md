# BRIEFING — 2026-06-18T11:55:00-06:00

## Mission

Optimize Sovereign Stack LLM execution parameters (context size, process-compose config, autostart) and compile the `lucebox-hub` library with Ampere TMA Emulation optimizations.

## 🔒 My Identity

- Archetype: Project Orchestrator
- Roles: orchestrator, user_liaison, human_reporter, successor
- Working directory: /home/toxic/sovereign/.agents/orchestrator
- Original parent: main agent
- Original parent conversation ID: 0071f912-89cb-42e6-94f6-994e66f782f6

## 🔒 My Workflow

- **Pattern**: Project Pattern
- **Scope document**: /home/toxic/sovereign/PROJECT.md

1. **Decompose**: Decomposed the user request into 3 sequential/parallel milestones tracked in PROJECT.md.
2. **Dispatch & Execute**:
   - **Direct (iteration loop)**: For each milestone, spawn Explorer(s) → Worker → Reviewer(s) → gate.
   - **Delegate (sub-orchestrator)**: Spawn sub-orchestrators for complex milestones.
3. **On failure** (in this order):
   - Retry: nudge stuck agent or re-send task
   - Replace: spawn fresh agent with partial progress
   - Skip: proceed without (only if non-critical)
   - Redistribute: split stuck agent's remaining work
   - Redesign: re-partition decomposition
   - Escalate: report to parent (sub-orchestrators only, last resort)
4. **Succession**: Self-succeed at 16 spawns. Write handoff.md, spawn successor, and exit.

- **Work items**:
  1. Context Tuning & Service Setup [pending]
  2. MTProto Service Integration [pending]
  3. Compile lucebox-hub [pending]
- **Current phase**: 1
- **Current focus**: Context Tuning & Service Setup

## 🔒 Key Constraints

- Never write, modify, or create source code files directly.
- Never run build/test commands yourself — require workers to do so.
- You may use file-editing tools only for metadata/state files (.md) in your .agents/ folder.
- Never reuse a subagent after it has delivered its handoff — always spawn fresh.

## Current Parent

- Conversation ID: 0071f912-89cb-42e6-94f6-994e66f782f6
- Updated: not yet

## Key Decisions Made

- Organized the tasks into three distinct milestones.

## Team Roster

| Agent           | Type     | Work Item      | Status    | Conv ID                              |
| --------------- | -------- | -------------- | --------- | ------------------------------------ |
| Explorer M1 (1) | explorer | M1 exploration | completed | 90501c2e-6213-4314-975e-fe17c0ab408a |
| Explorer M1 (2) | explorer | M1 exploration | completed | 5194f2ba-139d-488c-b8a1-771aca1f66ff |
| Explorer M1 (3) | explorer | M1 exploration | completed | fd786a7b-9a26-4e95-81d9-ea7837ec3b83 |
| Worker M1       | worker   | M1 execution   | completed | ae098db6-28ae-4a9f-a089-9959cc934abb |
| Reviewer M1 (1) | reviewer | M1 review      | cancelled | 2bd29ddb-2dab-4ed1-b384-a3647616fec9 |
| Reviewer M1 (2) | reviewer | M1 review      | cancelled | 5ef989c1-6386-4a79-9e8d-7fd8b79186cf |
| Auditor M1      | auditor  | M1 audit       | cancelled | ed1aef77-bea6-4e61-93d6-8d5a6d8ed58e |
| Explorer M3 (1) | explorer | M3 exploration | completed | 09dbad2b-7f85-4808-91ec-4805a6c757a0 |
| Explorer M3 (2) | explorer | M3 exploration | completed | 284ecbd1-b5cf-4296-a39c-d7babc9423ee |
| Explorer M3 (3) | explorer | M3 exploration | completed | 332bec4d-9d28-4d01-9205-9309f778165b |
| Worker M3       | worker   | M3 execution   | pending   | 4f4ffb2a-4b89-46ab-8ef8-7a7ad32359d2 |
| Explorer M2 (1) | explorer | M2 exploration | pending   | 497c3238-32fd-4a31-b73b-e8089f5c44a4 |
| Explorer M2 (2) | explorer | M2 exploration | pending   | 32f7ec1d-2546-4444-99e5-5833f5e68ddc |
| Explorer M2 (3) | explorer | M2 exploration | pending   | 1a360155-f225-4882-88aa-8e256147791b |

## Succession Status

- Succession required: no
- Spawn count: 14 / 16
- Pending subagents: 4f4ffb2a-4b89-46ab-8ef8-7a7ad32359d2, 497c3238-32fd-4a31-b73b-e8089f5c44a4, 32f7ec1d-2546-4444-99e5-5833f5e68ddc, 1a360155-f225-4882-88aa-8e256147791b
- Predecessor: none
- Successor: not yet spawned

## Active Timers

- Heartbeat cron: task-58
- Safety timer: none
- On succession: kill all timers before spawning successor
- On context truncation: run `manage_task(Action="list")` — re-create if missing

## Artifact Index

- /home/toxic/sovereign/PROJECT.md — Global index, architecture, milestones, contracts.
- /home/toxic/sovereign/ORIGINAL_REQUEST.md — Original verbatim user request.
