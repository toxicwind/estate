# AGENTS.md

Guidance for agents working on this repository.

## What this repo is

`airspeak` is a writing-style lint addon for AI agents. The repo root is an omp marketplace (`.omp-plugin/marketplace.json`); the installable addon lives in `plugin/`.

## Layout

- `plugin/src/index.ts` — the lint extension. Pure check functions at module scope (exported and unit-tested); `airspeak(pi)` is the default export the agent loads.
- `plugin/skills/airspeak/SKILL.md` — the portable Agent Skills document (frontmatter + body). Same content as the bundled skill.
- `plugin/tests/` — `bun test` runner. Fixtures live in `tests/fixtures/` (`corpus.json` for samples, `baseline.json` for the pinned issue lists).
- `specs/001-publish-ste-addon/` — design / data-model / task artifacts. Gitignored, not shipped.

## Conventions

- One language: English (ASD-STE100 Issue 9 mechanical subset).
- Rules are mechanical and machine-checkable. Word lists and string constants live at the top of `src/index.ts`.
- Thresholds are exported so tests can read them; do not hard-code duplicates.

## Testing

```sh
cd plugin
bun run typecheck
bun test
```

The packaging smoke tests spawn the real `omp` CLI and take ~20–30s per
install. bun 1.4 ignores bunfig `[test]` timeout keys, so the `--timeout`
flag lives in the `test` script — run `bun run test` (or `bun test
--timeout=120000`), not bare `bun test`, or the packaging suite dies at the
5s default.

## Release process

The version is `plugin/package.json` — every other version field derives from it. To release:

```sh
cd plugin
npm version <X.Y.Z>   # bumps package.json, syncs SKILL.md (both copies) + marketplace.json, commits, tags
git push && git push --tags
npm publish
```

`scripts/sync-version.mjs` keeps all version fields in sync: it runs on `npm version` (staged into the release commit) and `prepublishOnly` fails the publish if anything drifted. Write the changelog entry (`plugin/CHANGELOG.md`, `## [X.Y.Z] - YYYY-MM-DD`) before running `npm version`.
