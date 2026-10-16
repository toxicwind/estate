---
name: audit-skills
description: >-
  Audit a directory of skills for visibility, deterministic vs
  non-deterministic behavior, and composability. Use when the user wants to
  review, assess, or improve a skill collection. Produces a structured
  report with per-skill ratings and cross-cutting findings.
---

# Skill Auditor

Systematically evaluate a skills directory against three dimensions:
**visibility**, **determinism**, and **composability**.

## Arguments

- **skills directory** (required if ambiguous): Path to the directory
  containing skill subdirectories. If omitted, default to `./skills/`. The
  path can be absolute or relative and may point to any skills collection,
  not just the current project's.

## Step-by-step workflow

### 1. Discover skills

List every immediate subdirectory in the target directory. Treat each
subdirectory as a candidate skill. Verify that a `SKILL.md` file exists
inside it. Report any subdirectories that lack `SKILL.md` as
**unstructured entries** and skip them from the detailed audit.

### 2. Read every SKILL.md

Load each `SKILL.md` in full. If a skill has a `references/` or `scripts/`
subdirectory, note the presence of supplementary files but do not require
reading all of them unless they are critical to assessing the three
dimensions.

### 3. Assess per skill

For every skill, assign a rating and brief rationale for each dimension.

#### Visibility

Evaluate how clearly the skill communicates its contract to an agent that
has never used it before.

- **Excellent:** Explicit trigger phrases, input/output contracts, step-by-step
  workflow, constraints, output format with examples, and clear scope
  boundaries.
- **Good:** Clear purpose and workflow, but missing one of: structured input
  contract, output schema, or concrete examples.
- **Moderate:** Purpose is stated but workflow is vague, inputs are inferred
  from context rather than declared, or stop conditions are implicit.
- **Poor:** Purpose is unclear, no workflow is provided, or the skill is
  indistinguishable from a generic system prompt.

Evidence to inspect:
- YAML frontmatter `description` quality and specificity.
- Presence of explicit trigger phrases or invocation conditions.
- Structured workflow with numbered steps.
- Explicit constraints (read-only vs. mutating, human-in-the-loop vs.
  autonomous).
- Output format specification (template, schema, or example).

#### Determinism

Evaluate whether repeated invocations with identical inputs would produce
identical outputs and side effects.

- **Deterministic:** Behavior is fully specified by rules, templates, or
  scripts. No LLM sampling governs the core logic. External state, if any,
  is read-only or version-locked.
- **Mostly deterministic:** Core mechanics are deterministic but an LLM
  summarizes, classifies, or paraphrases within a rigid structure. Variance
  is bounded and cosmetic.
- **Mixed:** Some steps are scripted (file discovery, command execution) while
  others are LLM-synthesized (assessment, ranking, creative generation).
- **Non-deterministic:** The primary output is produced by LLM reasoning,
  synthesis, or judgment with no structural guardrails. Two runs on the same
  input may diverge significantly.

Evidence to inspect:
- Does the skill execute fixed commands (`bash`, `read`) in a fixed order?
- Does the skill instruct the LLM to "analyze," "evaluate," "rank," or
  "synthesize" without structured rubrics?
- Does it depend on time-varying external data (APIs, calendars, databases)?
- Does it mutate external state (files, tickets, tasks) based on LLM
  judgment?

#### Composability

Evaluate how easily the skill can be chained with other skills in an
automated pipeline.

- **High:** Clean input/output contract, pure (read-only) or idempotent,
  produces structured or machine-parseable output, no human-in-the-loop
  checkpoints, minimal external dependencies.
- **Moderate:** Output is prose or markdown (human-readable but not
  machine-parseable), or it has side effects that are predictable and
  documented, or it depends on one specific external tool.
- **Low:** Requires human approval mid-flow, is an open-ended creative task
  with no defined endpoint, or its output cannot be consumed by a downstream
  step.

Evidence to inspect:
- Does the skill stop and wait for user approval before proceeding?
- Is the output a rigid template, or freeform prose?
- Are there explicit hand-off patterns (e.g., "pass forward to X")?
- Does the skill mutate state in a way that would break a downstream skill
  if run twice?

### 4. Synthesize cross-cutting findings

After rating every skill, look for patterns across the directory:

1. **Structured output gaps:** How many skills emit prose rather than
   machine-parseable data (JSON, YAML, or strict markdown templates)? This
   limits chaining.
2. **LLM judgment as hidden variable:** Which skills are non-deterministic
   because their core work is reasoning rather than execution? Is there any
   seeding or versioning mechanism?
3. **Tool coupling:** Which skills are tightly bound to specific external
   tools (APIs, CLIs, services)? Are dependencies abstracted?
4. **Statefulness vs. purity:** Which skills mutate external state vs. which
   are read-only? Stateful skills compose less safely.
5. **Interface inconsistency:** Do skills use consistent patterns for
   arguments, defaults, and invocation? Or does each skill reinvent its own
   convention?

### 5. Produce the report

Write the report using the exact output format below. For directories with
more than a few skills, save the report to `SKILL_AUDIT.md` in the project
root. Always provide a brief summary in chat.

## Output format

### Chat summary (always)

One paragraph summarizing:
- The directory audited and number of skills reviewed
- Overall visibility, determinism, and composability levels
- The top 2–3 cross-cutting issues

### Full report (file or inline)

```markdown
# Skill Audit: [Directory Name]

**Directory:** [path/to/skills/]
**Skills reviewed:** [N]
**Unstructured entries:** [N subdirectories without SKILL.md, or "None"]
**Audit date:** [Date]

---

## Summary

[Brief narrative of overall health: strongest dimension, weakest dimension,
and the pattern that most limits the collection.]

---

## Per-Skill Ratings

| Skill | Visibility | Determinism | Composability |
|---|---|---|---|
| [name] | [Excellent/Good/Moderate/Poor] | [Deterministic/Mostly/Mixed/Non] | [High/Moderate/Low] |

### [Skill Name]

**Visibility:** [Rating] — [Rationale: what is present or missing.]

**Determinism:** [Rating] — [Rationale: what drives variance.]

**Composability:** [Rating] — [Rationale: can it be chained?]

---

## Cross-Cutting Findings

### [Issue Category]

**Finding:** [Description of the pattern.]

**Affected skills:** [List or "All"]

**Impact:** [How this limits the collection.]

**Recommendation:** [Concrete next step to improve.]

---
```

Repeat the issue template for every cross-cutting finding.

## Constraints

- Base every rating on explicit evidence from the skill's `SKILL.md`.
- Quote the skill's description or workflow when asserting a visibility gap.
- Do not inflate ratings. A skill with no explicit output format is not
  "Excellent" on visibility, even if its prose is well-written.
- A skill that waits for user approval is automatically capped at
  "Moderate" on composability, regardless of other virtues.
- A skill whose primary output is LLM-synthesized prose is automatically
  "Non-deterministic" or "Mixed," even if its discovery steps are scripted.
- Include unstructured entries in the report. They are a signal about
  directory hygiene.
