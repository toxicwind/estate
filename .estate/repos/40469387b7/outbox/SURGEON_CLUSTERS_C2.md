# SURGEON MUTATION CLUSTERS (C2) - 40469387b7

meta: repo_root=/home/toxic/development/estate, repo_hash=40469387b7, run_id=20261016T030439Z-27f514
agent_id=e5b8cab5, cycle=2, PE=pe_78b1e680b4774e5a, base=main@24fe5bb, anchor=tag pre-cluster (2d9b5cb)
toolchain: git 2.55.0 / python 3.14.7. Tracked now: .gitignore, README.md, tests/smoke_test.sh (tree clean).
Every cluster rollback (git only): git reset --hard pre-cluster && git clean -fd  (NEVER -x; .estate/ is ignored, survives).
All commands run from repo root. Identity-free commits: git -c user.name=estate-forge -c user.email=forge@awrawr-pc.

[CHR|40469387b7|e5b8cab5|SURGEON|20261016T030439Z-27f514|2|SURGERY|L00001] {"cluster":"A","kind":"guardrail","files":["tests/smoke_test.sh"],"proof":"bash tests/smoke_test.sh"}
[CHR|40469387b7|e5b8cab5|SURGEON|20261016T030439Z-27f514|2|SURGERY|L00002] {"cluster":"B","kind":"deferred_layer","files":["src/estate/__init__.py","pyproject.toml","tests/test_smoke.py"],"proof":"python3 tests/test_smoke.py"}
[CHR|40469387b7|e5b8cab5|SURGEON|20261016T030439Z-27f514|2|SURGERY|L00003] {"cluster":"C","kind":"governance","files":["LICENSE","CHANGELOG.md"],"proof":"git status -sb"}

## CLUSTER A - GUARDRAIL (harden smoke_test.sh; keep SMOKE_OK / exit 0)
(a) Target files: tests/smoke_test.sh (overwrite, keep mode 0755).
(b) Patch intent - write tests/smoke_test.sh verbatim:
    #!/usr/bin/env bash
    set -euo pipefail
    [ -f README.md ]  || { echo "FAIL: README.md missing" >&2; exit 1; }
    [ -f .gitignore ] || { echo "FAIL: .gitignore missing" >&2; exit 1; }
    if git ls-files | grep -q "\.estate/"; then echo "FAIL: .estate/ tracked" >&2; exit 1; fi
    echo SMOKE_OK
    exit 0
    Commit: git add -A && git -c user.name=estate-forge -c user.email=forge@awrawr-pc commit -m "cluster-a guardrail smoke"
(c) proof_cmd: bash tests/smoke_test.sh   (expect SMOKE_OK, exit 0)
(d) rollback: git reset --hard pre-cluster && git clean -fd

## CLUSTER B - DEFERRED LAYER (python package + pyproject; pytest-free import check)
(a) Target files: src/estate/__init__.py, pyproject.toml, tests/test_smoke.py.
(b) Patch intent - write verbatim:
    src/estate/__init__.py:
      """estate package."""
      __version__ = "0.1.0"
    pyproject.toml:
      [build-system]
      requires = ["setuptools>=61"]
      build-backend = "setuptools.build_meta"

      [project]
      name = "estate"
      version = "0.1.0"
      requires-python = ">=3.10"

      [tool.setuptools]
      packages = ["estate"]
    tests/test_smoke.py:
      import sys, pathlib
      sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
      import estate
      assert estate.__version__ == "0.1.0"
      print("PYTEST_FREE_OK")
    Commit: git add -A && git -c user.name=estate-forge -c user.email=forge@awrawr-pc commit -m "cluster-b deferred layer"
(c) proof_cmd: python3 tests/test_smoke.py   (expect PYTEST_FREE_OK, exit 0; git status -sb stays clean)
(d) rollback: git reset --hard pre-cluster && git clean -fd

## CLUSTER C - GOVERNANCE (LICENSE MIT-2026 + CHANGELOG cycle-1 entry)
(a) Target files: LICENSE, CHANGELOG.md.
(b) Patch intent - write verbatim:
    LICENSE (MIT, full text):
      MIT License

      Copyright (c) 2026 estate-forge

      Permission is hereby granted, free of charge, to any person obtaining a copy
      of this software and associated documentation files (the "Software"), to deal
      in the Software without restriction, including without limitation the rights
      to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
      copies of the Software, and to permit persons to whom the Software is
      furnished to do so, subject to the following conditions:

      The above copyright notice and this permission notice shall be included in all
      copies or substantial portions of the Software.

      THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
      IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
      FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
      AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
      LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
      OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
      SOFTWARE.
    CHANGELOG.md:
      # Changelog

      ## [Cycle 1] - 2026-10-16
      ### Added
      - Minimal scaffold: README.md, .gitignore, tests/smoke_test.sh (SMOKE_OK).
    Commit: git add -A && git -c user.name=estate-forge -c user.email=forge@awrawr-pc commit -m "cluster-c governance"
(c) proof_cmd: git status -sb   (expect `## main` header, clean tree, LICENSE + CHANGELOG.md tracked)
(d) rollback: git reset --hard pre-cluster && git clean -fd

## SELF-SCORING (1-5)
| cluster | proofability | locality | non-regression | notes |
|---|---|---|---|---|
| A | 5 | 5 | 5 | behavioral guardrail; fails loudly on missing files / tracked .estate |
| B | 4 | 4 | 5 | python proof via sys.path shim; purely additive (new dirs/files) |
| C | 5 | 5 | 5 | git-native clean-tree proof; pure add, no code touched |

## SYNTH PICK
Expect SYNTH to pick **Cluster A**: top proofability (fails loudly) + zero-regression, smallest surface; B and C are safe additive follow-ons.
