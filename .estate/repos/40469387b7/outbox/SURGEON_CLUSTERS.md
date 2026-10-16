# SURGEON MUTATION CLUSTERS - 40469387b7

meta: repo_root=/home/toxic/development/estate, repo_hash=40469387b7, run_id=20261016T030439Z-27f514
agent_id=e5b8cab5, cycle=1, PE=pe_ce21ca2b8454b434, toolchain=git 2.55.0 / python 3.14.7
baseline: NOT_A_GIT_REPO (no .git, zero tracked files, only .estate/ skeleton). All three clusters are first-commit builds; rollback anchor is a sentinel empty commit, not a parent sha.

## BASELINE SENTINEL (apply once, before any cluster)
Target: (none - git object only)
Intent: `git init -b main` (fallback `git init` + `git checkout -b main`), then
`git -c user.name=estate-forge -c user.email=forge@awrawr-pc commit --allow-empty -m baseline-cycle1`,
then `git tag pre-cluster`. This is the rollback anchor; it also proves identity-free commits work.
Proof: `git status -sb` (expect `## main` header, clean tree, zero staged entries).

## CLUSTER A ? MINIMAL SCAFFOLD
(a) Files created: README.md; .gitignore; tests/smoke_test.sh (chmod +x).
(b) Patch intent, verbatim-applyable:
- README.md: line1 `# estate`; line2 blank; then exactly 3 purpose lines:
  `Chronos Forge cycle-1 scaffold repository.`
  `It holds the minimal smoke-checkable layout for this repo.`
  `It is the baseline every later cycle mutates.`
- .gitignore: exactly 3 lines: `.estate/`, `__pycache__/`, `*.pyc`
- tests/smoke_test.sh: shebang `#!/usr/bin/env bash`; `set -euo pipefail`;
  `echo SMOKE_OK`; `exit 0`. Mode 0755.
- Then: `git add -A`; `git -c user.name=estate-forge -c user.email=forge@awrawr-pc commit -m cluster-a minimal scaffold`
(c) proof_cmd: `git status -sb` ? expect a `## main...` line plus a clean tree
  (no staged/modified entries; in a remote-less repo the header prints as `## main`).
(d) rollback (git only): `git reset --hard pre-cluster && git clean -fd`
  (`git clean` without `-x` honours .gitignore, so .estate/ survives untouched).

## CLUSTER B ? FULLER LAYOUT
(a) Files created: everything in A, plus src/estate/__init__.py, pyproject.toml, tests/test_smoke.py.
(b) Patch intent:
- README.md / .gitignore / tests/smoke_test.sh: identical to Cluster A.
- src/estate/__init__.py: 2 lines: `"""estate package."""` and `__version__ = "0.1.0"`
- pyproject.toml: minimal, name=estate, requires-python>=3.10:
  `[build-system]` / `requires = ["setuptools>=61"]` / `build-backend = "setuptools.build_meta"`
  / `[project]` / `name = "estate"` / `version = "0.1.0"` / `requires-python = ">=3.10"`
  / `[tool.setuptools]` / `packages = ["estate"]`
- tests/test_smoke.py: pytest-free, plain asserts, run via `python3`:
  `import estate` / `assert estate.__version__ == "0.1.0"` / `print("PYTEST_FREE_OK")`
  (needs `src` on sys.path, so the script begins with
  `import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))`)
- Then: `git add -A`; `git -c user.name=estate-forge -c user.email=forge@awrawr-pc commit -m cluster-b fuller layout`
(c) proof_cmd: `git status -sb` ? expect `## main...` line + clean tree.
(d) rollback (git only): `git reset --hard pre-cluster && git clean -fd`.

## CLUSTER C ? STATE-ONLY MINIMAL
(a) Files created: README.md only. No .gitignore, no tests/, no src/.
(b) Patch intent:
- README.md: single line `# estate` plus one line `Chronos Forge scaffold, cycle 1.`
- Then: `git add -A`; `git -c user.name=estate-forge -c user.email=forge@awrawr-pc commit -m cluster-c state-only minimal`
- Consequence: `.estate/` stays untracked-but-visible, so `git status -sb` is NOT clean;
  C therefore only self-consistent if proof is read as `## main...` + README tracked (see scoring).
(c) proof_cmd: `git status -sb` ? expect `## main...` line; tree is clean only w.r.t. README.md.
(d) rollback (git only): `git reset --hard pre-cluster && git clean -fd`
  (must NOT use `-x`; with no .gitignore, `.estate/` is untracked, so `git clean -fd` alone
  would remove it ? rollback for C must be `git reset --hard pre-cluster` ONLY).

## SELF-SCORING (1-5)
| cluster | proofability | locality | non-regression | notes |
|---|---|---|---|---|
| A | 5 | 5 | 5 | proof is git-native; smoke test is deterministic |
| B | 4 | 4 | 4 | proof still git-native; python check needs sys.path shim |
| C | 2 | 5 | 4 | no .gitignore leaves .estate/ dirty; weakest proof |

## SYNTH PICK
Expect SYNTH to pick **Cluster A**: it is the only cluster whose proof_cmd (`git status -sb`)
returns an unambiguously clean tree while adding the smallest, fully self-verifying payload.

## DRIFT RESILIENCE (observed during probe)
A concurrent expert briefly created then removed `.git`; root is back to `.estate/`-only.
Re-probe before applying: if `git -C $repo_root rev-parse --git-dir` succeeds, SKIP the
baseline sentinel and anchor rollback on the existing HEAD (`git tag pre-cluster` only).
If it fails, apply the sentinel block above. Do not force-reset a repo you did not create.
