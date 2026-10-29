# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Workspace jail** in `extensions/pi/jail.ts`: the shipped Pi
  extension now wires the vendored patcher against a `JailedNode-
  Filesystem` rooted at `process.cwd()`. Every path a section header,
  `MV DEST`, `REM`, or tag-based path recovery names is resolved
  against the root and refused if it escapes — lexically (absolute
  path, `..` traversal) or via a symlink whose realpath lands outside
  the root. Enforced at three checkpoints: sync `canonicalPath`, async
  `preflightWrite`, and `allowTagPathRecovery`. See
  `test/jail.test.ts` for the adversarial matrix (absolute-path SWAP,
  `..` traversal SWAP, `MV DEST` to absolute path, `MV DEST` via `..`,
  symlink-file escape, symlink-dir escape, symlink into an in-root
  dir *not* refused, tag-based recovery does not jump out of root,
  plus positive controls that ordinary in-root create/update/delete/
  move still succeed).
- `THIRD_PARTY_NOTICES.md` naming the exact upstream source for
  `src/vendor/`: `@oh-my-pi/hashline@16.2.13` by Can Boluk from
  `https://github.com/can1357/oh-my-pi/tree/main/packages/hashline`.
- `docs/tutorial.md` — first-run walkthrough for the Pi agent + human
  author.
- `docs/explanation.md` — design rationale for the tag-based anchor
  model, the preflight-vs-commit atomicity trade-off, and the 4-hex
  tag collision math.
- GitHub-only distribution scaffolding: `.github/workflows/check.yml`,
  issue templates (bug, feature, security link), and a PR template.
- `repository`, `bugs`, and `homepage` fields in `package.json`
  pointing at `acoyfellow/hashline-pi` so security advisories and
  security-txt-style lookups resolve to a real endpoint.

### Changed

- `LICENSE` now names both the repository-glue copyright (Jordan
  Coeyman) and the vendored-core copyright (Can Boluk and the
  oh-my-pi contributors) and directs readers to
  `THIRD_PARTY_NOTICES.md` for derivation detail. The prior "with
  the author's permission" phrasing has been replaced with an
  explicit upstream pointer.
- `SECURITY.md` and `README.md` "Guarantees" section now describe the
  workspace jail as an enforced property, not a documented limitation.
  The pre-jail statement that `MV DEST` traversal was in-scope has
  been replaced with an accurate description of what the jail
  enforces and what remains out of scope (the core FS seam, which is
  still not sandboxed by design and is not what this extension ships).
- The block-op warning message and README now match the actual
  behavior: `SWAP.BLK` and `DEL.BLK` **hard-fail** with an explicit
  fallback message; `INS.BLK.POST` **lowers to `INS.POST` with a
  warning**. The prompt (`src/vendor/prompt.md`) carries the same
  v1 caveat so the model does not attempt block variants it cannot
  serve.
- The extension's block-op detector no longer produces false positives
  on body-text mentions (`+// see SWAP.BLK docs`); it now walks
  lines and inspects the first token of each non-body row.
- `CONTRIBUTING.md` and `docs/how-to.md` no longer describe an
  npm-publish flow; the CI gate is documented as the CI gate.
- `package.json` `files` field now includes `THIRD_PARTY_NOTICES.md`,
  `SECURITY.md`, and `CHANGELOG.md` in the shipped tarball for
  consumers who install from a git tag.

### Security

- The primary attack shapes documented in the pre-release review —
  arbitrary file write via absolute-path section header, arbitrary
  file delete via `REM` on an out-of-root path, arbitrary file write
  via `MV DEST` traversal, symlink-based escape — are now refused by
  the shipped Pi extension. See `test/jail.test.ts`.

## [0.0.1] — 2026-07-03

### Added

- Initial public release. Ships a single Pi extension registering the
  `hashline` tool.
- Vendored hashline core under `src/vendor/`: tokenizer, parser,
  applier, patcher, snapshot store, recovery, streaming line
  formatter, diff-preview builder, and the model-facing prompt.
- Adversarial test suite covering stale tags, malformed and
  overlapping headers, multi-hunk and multi-file atomicity, unicode
  and CRLF preservation, `MV`/`REM` semantics, and unsupported block
  ops. Note that the "path traversal" line in the original release
  notes was misleading — the core FS abstraction was not sandboxed,
  and that test documented the escape rather than blocking it. The
  Unreleased section above records the actual jail behavior that
  ships in the current tree.
