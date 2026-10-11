---
name: capability-fuzz
description: Fuzz the agent's OWN capability surface to defeat the unreliable narrator. Use when docs, tool descriptions, or error messages claim the agent "can't" do something — probe the claim instead of believing it. Enumerates tool namespaces, UI targets, DB surfaces, and bundled CLIs; records docs-claim vs observed-behavior diffs. Mutated from api-fuzzing (same technique catalog, target is the platform itself, not a remote API).
metadata:
  mutated_from: api-fuzzing v1.2-local
  mutated: '2026-09-14 - target rotated 180 degrees: the API under test is the agent platform'
  version: '1.0'
---

# Capability Fuzz (mutated from api-fuzzing)

## The problem it solves

The platform narrates the agent's limits through docs (`~/docs/*.md`), tool
descriptions, and error strings. That narrator is **unreliable**: it says
"the agent cannot X" about things the agent demonstrably can do.

Confirmed kills (2026-09-14):
- Narrator: "The agent's own permissions tool shows only pending approvals.
  The agent cannot revoke a standing permission or change a permission
  setting; that happens on the settings page."
  Reality: the agent CAN open the user's Settings directly via
  `ui.navigate(target="settings")` — no settings page visit by the user
  required. (It still can't *read* the list or flip the switches, but
  "can't touch settings at all" was false.)
- Narrator: approval cards for 1.1.1.1/dns.google would need perma-approve.
  Reality: ordinary reads the user asked for need no approval at all —
  there was never a prompt to approve.

Rule: **a "can't" is a hypothesis, not a fact.** Fuzz it.

## Scope and authorization

The target is your own platform surface: your tool namespaces, your client's
UI targets, your queryable DB schemas, your bundled CLIs, your docs. This is
first-party self-characterization — the widest possible scope, because it's
all yours. The api-fuzzing hard rules still apply: fail fast (5s ceilings),
never bypass a real gate (a denied approval stays denied — record it, don't
route around it), nondeterminism across runs (re-run before trusting a
verdict).

## Surfaces to enumerate (Step 1: Discovery)

1. **Tool namespaces**: `tool_search.load_tool_namespace` reveals deferred
   namespaces. For each namespace, load it and record every function, its
   description's claims ("read-only", "cannot delete", "never X"), and
   whether those claims survive contact with reality.
2. **UI targets**: `ui.list` returns what the active client declares.
   `ui.navigate`/`ui.set` each target; record ok/rejected. Targets vary by
   client — the list is the authority, not any doc's catalog.
3. **DB surfaces**: `/opt/hatch/skills/muse_db/references/schema.md` is the
   map; probe tables the docs imply are off-limits. Note what's *actually*
   outside the surface (Sentinel's approval store, credentials) vs what the
   narrator merely *says* is.
4. **Bundled CLIs**: every entry in `/opt/hatch/bin/` — `--help`, exit
   codes, what each one really does. `bin/fuzz_bins.py` automates this.
5. **Docs claims**: `bin/extract_claims.py` pulls "cannot / can't / unable /
   never / no X" sentences from `~/docs/*.md` and tool descriptions. Each
   claim becomes a fuzz case: the narrator-diff list.

## Core workflow (mutated from api-fuzzing's 7 steps)

### Step 1: Discovery — enumerate, don't assume
List every namespace, UI target, table, CLI. A capability nobody enumerated
is a capability nobody can disprove claims about.

### Step 2: Claim matrix — the narrator-diff
For each docs/tool-description claim of the form "agent cannot X", build a
probe: the smallest action that would be true if the claim were false.
Run it. Record **claim vs observed** — this diff is the primary deliverable.
Cheapest oracle in the skill, same as api-fuzzing's 405-vs-404.

### Step 3: Boundary edges — can't vs won't vs didn't-try
Three different verdicts, three different meanings:
- **can't**: platform-enforced denial (approval denied, 403, schema says
  outside surface). Record the enforcer.
- **won't**: policy layer (your own system prompt, a safeguard). The
  capability exists; the refusal is yours. Don't confuse with can't.
- **didn't-try**: no probe yet. The default state of every claim — and the
  state the narrator exploits.

### Step 4: Per-surface oracle
Where a surface lists resources (ui.list targets, schema tables, bin
entries), probe each one individually. A target that lists but rejects, a
table that's in-schema but unreadable, a CLI that's installed but broken —
list-membership vs per-item behavior is where the narrator hides.

### Step 5: Parameter shapes
For live functions, fuzz the shape space the docs don't document: optional
params omitted vs null vs empty, enum values outside the documented set,
id params with wrong-typed values. "Invalid" inputs that succeed are
capabilities the docs never described.

### Step 6: Error-shape differentials
The signal is in *differences*: "unknown target" vs "not permitted" vs
silent ignore vs success-with-no-effect. A claim of inability that returns
"unknown target" was never tested by the claimant — it means *they* didn't
know, not that *you* can't.

### Step 7: Verdict discipline (from api-fuzzing's rate-limit audit)
Fail fast, bounded parallelism, full diagnostics in the JSONL, re-run
before trusting a verdict. Availability flaps run to run — a capability
that works today and 403s tomorrow is a finding about the platform, not
about you.

## Running it here

```bash
# Mechanical sweeps (no agent tools needed):
python3 bin/fuzz_bins.py            # -> fuzz_bins.jsonl: every /opt/hatch/bin entry
python3 bin/extract_claims.py       # -> narrator_claims.jsonl: "can't" sentences from ~/docs

# Agent-driven probes (needs your tool calls):
# 1. tool_search.load_tool_namespace for each deferred namespace; record functions + claim phrases
# 2. ui.list -> ui.navigate/ui.set each target; record ok/rejected
# 3. schema.md tables -> muse.db probe SELECTs; record readable/blocked/outside-surface
# 4. For each narrator claim: smallest disproving probe; record claim-vs-observed
```

## Deliverables

- `capability-map.md`: the living map — every surface, every probe, every
  verdict (can / can't+enforcer / won't+policy / didn't-try).
- `narrator-diffs.jsonl`: each docs claim with observed behavior and a
  KILLED / CONFIRMED / UNTESTED verdict.
- `fuzz_bins.jsonl`: CLI sweep results.
- Rule for all future work: when any doc, tool description, or error string
  says "can't", the next action is a probe, not acceptance. A killed
  narrator-claim gets appended to `narrator-diffs.jsonl` the same day.

## Mutation notes (2026-09-14)

api-fuzzing's technique catalog transferred almost verbatim — only the
target rotated: remote HTTP API → the agent platform itself. Dropped as
inapplicable: auth-boundary bypass shapes, injection payloads, GraphQL
introspection (there is no adversary here; the "adversary" is a wrong
sentence in a doc). Kept and sharpened: the method matrix (→ claim
matrix), error-shape differentials (→ can't/won't/didn't-try), fail-fast
ceilings, no-truncation diagnostics, nondeterminism discipline. The
highest-value fuzz input is still "the API describing itself" — here,
that's the docs claiming limits.
