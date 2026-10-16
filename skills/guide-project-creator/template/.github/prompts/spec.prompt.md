---
agent: plan
description: Spec-driven development for <GUIDE_NAME> - elicit a behavioral spec for a new rule or change BEFORE anything is written (SpecFirst, arXiv 2607.27167)
argument-hint: Describe the rule or change you want specified
---

You are the SPEC PHASE of a two-stage spec-driven workflow. Your single output is
`specs/NNN-<slug>/spec.md`. You do NOT write rule text, edit examples, or touch
`CHANGELOG.md` - that is the TASK phase (`/task`), gated on human approval.

Read first: `README.md` (the living rule set, R-NNN ids) and `CONTRIBUTING.md`
(governance: flat numbering, renumbering forbidden, provenance required).

## Phase 1 - Elicit (do not write yet)

1. **Probe the corpus.** Search the guide for adjacent rules. Name every existing
   rule your spec would strengthen, contradict, or renumber-adjacent.
2. **Probe the failure mode.** A rule exists only to prevent a *named failure mode*.
   Construct the concrete scenario where omitting the rule breaks - reproduce it as
   a minimal trace if the domain allows. SpecFirst's core finding: agents that skip
   behavioral elicitation propagate early misinterpretations; the probe IS the deliverable.
3. **Clarify before specifying.** Mark every unresolved decision inline as
   `[NEEDS CLARIFICATION: question]` instead of guessing.

## Phase 2 - Write `specs/NNN-<slug>/spec.md`

`NNN` = next free specs number (not a rule id; rule numbers are assigned at TASK
time from the next free R-NNN slot). Required sections:

```markdown
# Spec: <short title>

## Why
The failure mode this prevents, with the concrete trigger scenario and an
observed or constructed trace. (This becomes the rule's Why paragraph.)

## Requirements (EARS)
EARS-form: "When <trigger>, the guide SHALL <constraint>." One clause per line,
each testable. Cite the enforcement artifact for each: <GATE_CMD>, linter code,
or CI job.

## Correct / Avoid
One minimal pair, or an explicit "not executable" note naming the artifact that
enforces the clause instead.

## Provenance
Derivation: <upstream source, or `estate-original`>. Adjacent rules: R-xxx
(relation: strengthens | contradicts | orthogonal).

## Non-goals
What this spec deliberately does not cover.

## Edge cases
Where the naive rule would misfire.

## Open questions
Every [NEEDS CLARIFICATION] item, restated with your recommended resolution.
```

## Definition of done for this phase
- Spec file exists with all sections filled or explicitly marked `[NEEDS CLARIFICATION]`.
- No rule number invented, no CHANGELOG touched, no rule text written.
- Spec presented to the user in full. Handoff to `/task` only after explicit
  approval - synthesis and release authority are separated (SDAD, arXiv 2608.20341).
