# Verification playbook

The plan is not done until you know the exact commands that prove the change
works. Resolve them in this order and stop at the first that applies.

## 1. Read the project's own scripts

| Ecosystem | Where the truth lives |
|---|---|
| Node | `package.json` → `scripts.test`, `scripts.build`, `scripts.lint`, `scripts.typecheck` |
| Python | `pyproject.toml` / `tox.ini` / `noxfile.py`; common: `pytest`, `ruff check`, `mypy` |
| Go | `go test ./...`, `go vet ./...`, `go build ./...` |
| Rust | `cargo test`, `cargo clippy`, `cargo build` |
| Make-based | `Makefile` targets: `test`, `lint`, `check`, `ci` |

## 2. Mirror what CI actually runs

CI is the source of truth for "green". Read `.github/workflows/*.yml` (or
`.gitlab-ci.yml`, `.circleci/config.yml`) and copy the exact install + test
sequence. If CI runs `npm ci && npm test`, your verification is `npm ci && npm test`, not what you would prefer.

## 3. Detect the package manager before suggesting install steps

- `package-lock.json` → npm (`npm ci`)
- `pnpm-lock.yaml` → pnpm (`pnpm install --frozen-lockfile`)
- `yarn.lock` → yarn (`yarn install --immutable`)
- `bun.lockb` → bun (`bun install`)

## 4. When nothing is discoverable

Do **not** fabricate a command. Emit a `manual_checks` entry and flag it:

```json
{
  "commands": [],
  "manual_checks": [
    "verification commands unspecified, no test/build script or CI workflow found; confirm with the maintainer"
  ]
}
```

## 5. Scope the verification to the change

A one-file fix needs the narrowest check that exercises it (one test file, one
type-check), not the whole suite, unless the change is cross-cutting. Match the
verification altitude to the change altitude.
