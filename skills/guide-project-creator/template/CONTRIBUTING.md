# Contributing to <GUIDE_NAME>

Rules are flat-numbered. New rules take the next free number in their
area. Renumbering is forbidden - downstream commits cite rule ids.

## Before you open a PR

1. Run the gate: `node bin/validate.js` - exit 0 required.
2. If your rule ships an executable Correct/Avoid pair, the gate checks the
   `examples/` tree; keep both halves minimal and ASCII-only.
3. Cite the rule your change enforces in the commit body. Example:
   `Enforce R-101 in <area>.`

## Adding a rule

- Cite the upstream you derive it from, or mark `estate-original`.
- Include a Correct / Avoid pair (or an explicit "not executable" note naming
  the enforcement artifact instead: linter code, CI job, validator check).
- Include a Why paragraph that names the failure mode the rule prevents.
- Add the rule to `CHANGELOG.md` under `[Unreleased]`.

## SDD workflow (preferred)

1. `/spec` - write `specs/NNN-<slug>/spec.md` (Plan agent; no code, no ids invented).
2. Human approves the spec.
3. `/task` - implement: rule text + gate wiring + CHANGELOG, each step
   ending with its proof command.
4. `/verifySpec` - independent verification; a FAIL returns findings, never patches.

## Adding an area

New areas extend the id space (`R-<area><n>`); document the area in the
README Rules section header and reserve the range in CHANGELOG.
