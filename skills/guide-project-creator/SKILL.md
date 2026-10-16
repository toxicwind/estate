---
name: guide-project-creator
description: "Scaffold a new awesome-style *-guide project (bash-style-guide pattern): flat R-NNN rule ids, provenance docs, Correct/Avoid examples, machine gate, SDD prompt trio. Creates the repo, commits, pushes to GitHub, and registers it in ranch."
---

# Guide Project Creator

Creates a first-class `*-guide` project following the estate guide convention
pioneered by `bash-style-guide` and reused by `agent-customization-style-guide`.

## Usage

```
new-guide.sh <slug> <github-owner> "<one-line description>"
```

Example:

```
new-guide.sh agent-customization-style-guide toxicwind \
  "A style guide for writing correct AGENTS.md, .prompt.md and .agent.md files"
```

## What it scaffolds (from template/)

- `README.md` - centered title + description, Contents list, rule sections with
  flat R-NNN ids, each rule: statement -> Why -> Correct/Avoid -> provenance.
- `CONTRIBUTING.md` - gate list (run before PR), how to add a rule (cite upstream
  or `estate-original`, Correct/Avoid pair, Why paragraph, CHANGELOG entry;
  renumbering forbidden).
- `CHANGELOG.md` - `[Unreleased]` ledger.
- `LICENSE` - MIT.
- `examples/good/` + `examples/bad/` - checked by the gate.
- `bin/validate.js` - the machine gate: runs on every file in the guide's scope
  and exits nonzero on any finding. Every guide MUST have at least one gate.
- `.github/prompts/spec.prompt.md`, `task.prompt.md`, `verifySpec.prompt.md` -
  the SDD trio (SpecFirst elicitation -> gated synthesis -> independent
  verification), genericized with `<GUIDE_NAME>` and `<GATE_CMD>` placeholders
  that the script fills in.

## Steps

1. Run `bin/new-guide.sh` - copies the template, substitutes placeholders,
   `git init`, initial commit.
2. Push: `git remote add origin git@github.com:<owner>/<slug>.git && git push -u origin main`.
3. Register in ranch: add a `.gitmodules` entry (submodule) or directory symlink
   per the ranch convention, then commit in ranch.
4. Fill the guide's actual rules - use the repo's own SDD trio
   (`/spec` -> `/task` -> `/verifySpec`). The guide dogfoods its own workflow.
5. Prove: run `node bin/validate.js` inside the new repo - exit 0 required.

## Rules of the convention (must hold in every created guide)

- Flat rule ids `R-<area><n>` - no renumbering, ever; commits cite ids.
- Every rule names the failure mode it prevents (Why paragraph).
- Every rule has a Correct/Avoid pair where the domain allows executable examples.
- Every guide ships >=1 machine gate; the gate is the proof command of the TASK phase.
- Provenance: each rule cites its upstream or is marked `estate-original`.
