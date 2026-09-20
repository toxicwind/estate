---
name: tau-session-audit
description: Audit tau session JSONL files - reconstruct user intent, track completion, flag anomalies, and generate next-step plans.
---
# tau-session-audit Skill: Track User Intent and Completion

## Purpose
Track what the user wanted, what was completed, and make a plan for next steps. Audits tau session JSONL files to reconstruct user intent and work done.

## When to Use
- Starting a new session: review prior sessions to understand what was attempted
- After interrupted work: reconstruct what was done and what's left
- Before planning next steps: audit recent sessions for context
- When switching between tasks: understand what completed vs. in-progress

## How to Use via TMUX

```bash
# 1. Run the audit to see what was completed
tau --skill tau-session-audit

# 2. Or run directly
bun run /home/toxic/sovereign/skills/tau-session-audit/helper/audit.ts

# 3. Or run with options
bun run /home/toxic/sovereign/skills/tau-session-audit/helper/audit.ts --all
bun run /home/toxic/sovereign/skills/tau-session-audit/helper/audit.ts --check plan
bun run /home/toxic/sovereign/skills/tau-session-audit/helper/audit.ts --check completed
bun run /home/toxic/sovereign/skills/tau-session-audit/helper/audit.ts --check intent
bun run /home/toxic/sovereign/skills/tau-session-audit/helper/audit.ts --verbose
```

## Audit Checks

The skill scans all `*.jsonl` files under `~/.tau/agent/sessions/` and reports:

### 1. User Intent Reconstruction
- Analyzes session titles, model changes, and event sequences
- Identifies what the user was working on (e.g., "Groq integration", "NVIDIA config", "session migration")
- Maps sessions to user goals

### 2. Completion Tracking
- Identifies completed work (session_init → session with results)
- Flags in-progress work (sessions with no clear completion signal)
- Detects interrupted work (near-empty sessions, compaction events)

### 3. Plan Generation
- Based on intent + completion, suggests next steps
- Identifies dependencies between sessions
- Flags blockers or missing context

### 4. Session Integrity
- **UNKNOWN_TYPES** — events with unrecognized type `?` (malformed JSONL)
- **NEAR_EMPTY** — sessions with ≤4 events (likely incomplete/interrupted)
- **HAS_COMPACTION** — sessions with compaction events (context was compressed)
- **CREDENTIAL_PIN** — sessions with credential_pin events
- **TTSR_INJECTION** — sessions with TTSR injection events
- **BRANCH_SUMMARY** — sessions with branch summary events
- **SESSION_INIT** — sessions with session_init events
- **MODE_CHANGE** — sessions with mode_change events
- **SERVICE_TIER_CHANGE** — sessions with service_tier_change events

## Exit Codes
- `0` — audit complete, plan generated
- `1` — critical anomalies found (unknown types, corrupted files)

## Example

```bash
# Review recent sessions before starting new work
tau --skill tau-session-audit --check intent --check completed --check plan

# Output:
# INTENT: Groq provider integration (Sep 7-8 sessions)
# COMPLETED: 12 sessions, 2,999 events in Groq integration session
# INCOMPLETE: 3 sessions with near-empty traces
# PLAN: 1. Verify Groq catalog sync  2. Fix remaining test failures  3. Update docs
```

## Files Audited
- `~/.tau/agent/sessions/**/*.jsonl` — all session JSONL files
- `~/.tau/agent/sessions/-*/**/__advisor.jsonl` — advisor sub-sessions
