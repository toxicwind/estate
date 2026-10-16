<div align="center">

# <GUIDE_NAME>

**<GUIDE_DESC>**

*Synthesised for the assisted-by-AI era. Rules carry flat R-NNN ids so they can be cited in code review, commit messages, and PR replies. Renumbering is forbidden.*

</div>

---

1. [Scope](#scope)
2. [Rules](#rules)
3. [Gates](#gates)
4. [Contributing](CONTRIBUTING.md)

---

## Scope

What this guide governs: `<fill in - file types, tools, and workflows covered>`.
What it deliberately does not: `<fill in>`.

## Rules

Rules are flat-numbered by area. Areas: `<R-1xx ...>`. Each rule carries:
a statement, a **Why** naming the failure mode it prevents, a **Correct/Avoid**
pair where the domain allows executable examples, and **Provenance** (the
upstream it derives from, or `estate-original`).

<!-- Add rule sections here. Use the repo's own /spec -> /task -> /verifySpec workflow. -->

## Gates

Every change must pass all gates before merge. Run from repo root:

```bash
node bin/validate.js
```

`bin/validate.js` is the canonical proof command of the TASK phase
(`.github/prompts/task.prompt.md`). A change is not done until the gate exits 0.

## SDD workflow

This repo dogfoods spec-driven development:

1. `/spec` - elicit a behavioral spec into `specs/NNN-<slug>/spec.md` (Plan agent, read-only).
2. `/task` - synthesize the rule + gate, one proof-gated step at a time.
3. `/verifySpec` - independent verification: Spec Fidelity + gate reproduction.

Synthesis and release authority are separated (SDAD, arXiv 2608.20341).
Elicitation precedes synthesis (SpecFirst, arXiv 2607.27167).
