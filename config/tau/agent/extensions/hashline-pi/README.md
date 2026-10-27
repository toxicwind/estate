# hashline-pi

A [Pi coding agent](https://www.npmjs.com/package/@earendil-works/pi-coding-agent)
extension that registers a `hashline` tool for line-anchored, tag-verified
file edits.

Hashline is a small patch language designed for LLM-authored edits. Every
patch section is anchored to a 4-hex content-hash tag minted from the file
the model just read, so a section written against stale content is rejected
with a re-read instruction instead of silently drifting. A patch that
touches multiple files is fully preflighted in memory before the first
write hits disk.

## Status

Version `0.0.1`. Distributed **from GitHub only** — this package is
intentionally `"private": true` in `package.json`. There is no npm-registry
release. Expect API churn in `0.x`.

## Provenance

The vendored core under `src/vendor/` is a re-formatted copy of
[`@oh-my-pi/hashline@16.2.13`](https://github.com/can1357/oh-my-pi/tree/main/packages/hashline)
by Can Boluk and the oh-my-pi contributors, redistributed here under its
declared MIT license. See `THIRD_PARTY_NOTICES.md` for the exact source,
version pointer, list of vendored files, and license text. The
`extensions/pi/` directory (Pi tool registration, workspace jail,
adversarial test wiring) is original to this repository and © 2026 Jordan
Coeyman.

## Install

Requires [Bun](https://bun.sh) 1.3+ and a Pi installation that supplies
`@earendil-works/pi-coding-agent` ≥ 0.80.0. This repository is
distributed as source; Pi 0.80.x's extension loader recognises three
shapes (`package.json.pi.extensions`, direct `.ts`/`.js` files, and
`subdir/index.ts` + optional `package.json`).

### Option A — clone into your Pi extensions directory

```sh
git clone https://github.com/acoyfellow/hashline-pi.git \
  ~/.tau/agent/extensions/hashline-pi
cd ~/.tau/agent/extensions/hashline-pi
bun install
```

Pi will discover the extension via the `pi.extensions` field in this
repository's `package.json`:

```json
{
  "pi": {
    "extensions": ["./extensions/pi/index.ts"]
  }
}
```

### Option B — clone anywhere and point Pi at it

```sh
git clone https://github.com/acoyfellow/hashline-pi.git
cd hashline-pi
bun install
```

Then either add the absolute path of this directory to your Pi config's
extension search paths, or drop a `pi.config` alias into
`~/.tau/agent/extensions/` that references it. The relative import from
`extensions/pi/index.ts` to `../../src/vendor/index.ts` assumes the
repository layout is preserved, so do not copy `extensions/pi/index.ts`
out of the repo without bringing `src/vendor/` along.

### What NOT to do

- Do not run `npm publish` / `bun publish`. The package is private and
  will refuse. Distribution is by clone only.
- Do not rewrite the section-header `#TAG` by hand to bypass a
  stale-tag rejection — the tag exists to catch exactly that drift.

## Patch language at a glance

Every section starts with `[PATH#TAG]`. `TAG` is a 4-hex snapshot fingerprint
of the file returned by the last `read`/`search`. It is required on every
section: hashline never creates files (use the `write` tool for that).

```
[src/foo.ts#A1B2]
SWAP 12.=14:
+  return next(input);
DEL 42
INS.POST 7:
+// added banner
```

Operations:

- `SWAP N.=M:` — replace inclusive line range `N.=M` with body rows.
- `DEL N` / `DEL N.=M` — delete a single line or an inclusive range.
- `INS.PRE N:` / `INS.POST N:` — insert body rows before/after line `N`.
- `INS.HEAD:` / `INS.TAIL:` — insert at start/end of file.
- `REM` — delete the whole file. No body, no line ops.
- `MV DEST` — rename/move the section file to `DEST`.

Body rows are literal lines prefixed with `+`. `+` alone adds a blank line.
There are no `-old` rows; the range already names what is being changed.

**Block ops are not fully supported in v1.** The parser accepts
`SWAP.BLK`, `DEL.BLK`, and `INS.BLK.POST` so the format is
forward-compatible, but no tree-sitter resolver is wired in this
extension:

- `SWAP.BLK` and `DEL.BLK` — **hard-fail** with the exact
  concrete-range fallback to use instead. There is no "silent warning"
  path.
- `INS.BLK.POST` — **lowers to plain `INS.POST` with a warning** so the
  patch still applies; verify the landing line.

See `src/vendor/prompt.md` for the full grammar the tool description
ships to the model and `docs/explanation.md` for the design rationale.

## Guarantees this extension enforces

- **Workspace jail.** Every path a section header (or `MV DEST`) names
  is resolved against the extension's workspace root (defaulting to
  `process.cwd()` at extension-init time) and refused if it escapes,
  including via absolute paths, `..` traversal, or symlinks whose
  realpath lands outside the root. See `extensions/pi/jail.ts` and the
  adversarial suite in `test/jail.test.ts`.
- **Every section carries a fresh tag.** The extension mints the
  current content hash for every in-jail target path before applying,
  so a stale tag is rejected with a clear "re-read the file" message
  before any write.
- **Multi-file patches are all-or-nothing at preflight.** All sections
  are parsed, tag-checked, and applied in memory before any commit
  runs. A parse error, stale tag, jail escape, or missing anchor line
  aborts the entire patch. Once commits start, a mid-batch write
  failure reports exactly which files landed and which did not — the
  extension does **not** roll back the sections that already
  committed. See `docs/explanation.md` for the preflight-vs-commit
  atomicity model.
- **Multiple sections targeting the same path are merged.** Anchors
  authored against the same snapshot must be applied as one batch;
  otherwise the first sub-edit shifts line numbers out from under the
  second's anchors.
- **Unsupported block ops fail loud (or lower loud).** `SWAP.BLK` and
  `DEL.BLK` throw with the exact fallback; `INS.BLK.POST` lowers to
  `INS.POST` with a warning. The wrapper never guesses a block
  boundary silently.
- **CRLF, BOM, and trailing-whitespace differences do not invalidate a
  tag.** The tag is computed over LF-normalized text with trailing
  `[ \t\r]` stripped from each line, and the original ending + BOM are
  restored on write.

## Development

```sh
bun install
bun run check   # biome + tsc --noEmit + bun test
bun run format
bun test
```

The test suite is split in two:

- `test/hashline.test.ts` — adversarial suite for the vendored core.
  Stale tags, malformed headers, overlap, cross-file atomicity,
  unicode/CRLF preservation, `MV`/`REM` semantics, unsupported block
  ops. This suite documents behavior of the generic `NodeFilesystem`
  seam, which is intentionally not sandboxed.
- `test/jail.test.ts` — adversarial suite for the shipped extension's
  workspace jail. Absolute-path headers, `..` traversal, `MV DEST`
  escape, symlink escape, tag-based path recovery refuses to jump out
  of root, plus positive controls that ordinary in-root edits still
  pass.

Continuous integration runs `bun run check` on every push and PR; see
`.github/workflows/check.yml`.

## Security

Report vulnerabilities via GitHub's private security advisory workflow
on this repository (`https://github.com/acoyfellow/hashline-pi/security/advisories/new`).
See `SECURITY.md` for scope.

## License

MIT — see `LICENSE`. The vendored core carries the same license; see
`THIRD_PARTY_NOTICES.md` for the derivation, upstream repo, and
copyright detail.
