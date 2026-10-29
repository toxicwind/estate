# Contributing to hashline-pi

Thanks for taking an interest. This is a small, focused Pi extension; the
bar for changes is proportionally high.

## Ground rules

- Open an issue before opening a large PR. Design discussion is cheap;
  code review of a large surprise is not.
- The vendored core under `src/vendor/` mirrors the upstream
  [`@oh-my-pi/hashline`](https://github.com/can1357/oh-my-pi/tree/main/packages/hashline)
  package (author: Can Boluk). Bug fixes to the core are welcome here,
  but please land the equivalent fix upstream too so this repository's
  copy can stay close to a known-good reference. See
  `THIRD_PARTY_NOTICES.md` for the vendored version and derivation
  detail.
- Keep behavior changes covered by a test in `test/`. The suites are
  deliberately adversarial — new features should extend that surface,
  not weaken it. Never delete an assertion to make a test pass; add
  the new case alongside.
- The workspace jail in `extensions/pi/jail.ts` is a security boundary.
  Changes to it require a matching entry in `test/jail.test.ts` proving
  the new behavior does not open an escape.
- Do not introduce new dependencies without justification. Every dep is
  a supply-chain surface that must survive the same review as the code.

## Local workflow

```sh
bun install
bun run check   # biome + tsc --noEmit + bun test
bun run format
```

`bun run check` is what CI runs (`.github/workflows/check.yml`). Please
make sure it is green locally before pushing.

## Distribution model

This repository is **GitHub-only**. `package.json` sets `"private":
true`; there is no npm-registry release, no `bun publish`. Consumers
install by cloning the repository into their Pi extensions directory.
Do not add "release" language to docs that describes an npm-publish
workflow — the CI gate exists to catch that a change did not break
consumers, not to gate a publish that will never happen.

## Style

- TypeScript, ES module syntax, Bun as the test runner.
- Biome for formatting and lint. Run `bun run format` before committing.
- Follow the existing comment style: short, factual, no marketing prose.
- Every exported symbol needs a JSDoc block that says what it does, when
  it fires, and any invariant it relies on.

## Reporting bugs

Include:

1. A minimal patch that reproduces the failure (paste it inline, redact
   any private paths).
2. The exact error message or wrong output.
3. Node / Bun version and the Pi version you are running under.

Security-sensitive bugs: see `SECURITY.md`. Do not paste a working
exploit into a public issue; use the private advisory workflow.
