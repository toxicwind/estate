## What this changes

A short description of the change and the motivating problem.

## Test coverage

- [ ] `bun run check` is green locally.
- [ ] Behavior changes are covered by a test in `test/`.
- [ ] If this touches `extensions/pi/jail.ts` or any code path a
      section header can reach, an adversarial test in
      `test/jail.test.ts` proves the change does not open a jail
      escape.
- [ ] If this touches `src/vendor/`, the equivalent fix is (or will be)
      landed upstream in
      [`@oh-my-pi/hashline`](https://github.com/can1357/oh-my-pi/tree/main/packages/hashline).

## Distribution / release notes

This repository is GitHub-only. `package.json` stays `"private": true`
and there is no npm publish step. If this change materially affects
consumers, add a `CHANGELOG.md` entry under the current unreleased
section.

## Security relevance

- [ ] This change is purely additive / documentation.
- [ ] This change modifies a security boundary (jail, tag verification,
      snapshot store, tag-based recovery). If ticked, describe the
      threat model impact.
