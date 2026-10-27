# Third-party notices

This document lists third-party code redistributed inside this repository
and the license terms that apply. It is a companion to `LICENSE`; when the
two disagree about a specific file, `THIRD_PARTY_NOTICES.md` wins.

## `src/vendor/` — hashline core

**Upstream package:** `@oh-my-pi/hashline`, version `16.2.13`.

**Upstream repository:** https://github.com/can1357/oh-my-pi
(subdirectory `packages/hashline`).

**Upstream author:** Can Boluk.

**Upstream license:** MIT.

**How this repository derives from upstream.** The 20 files under
`src/vendor/` (`apply.ts`, `block.ts`, `diff-preview.ts`, `format.ts`,
`fs.ts`, `grammar.lark`, `index.ts`, `input.ts`, `messages.ts`,
`mismatch.ts`, `normalize.ts`, `parser.ts`, `patcher.ts`, `prefixes.ts`,
`prompt.md`, `recovery.ts`, `snapshots.ts`, `stream.ts`, `tokenizer.ts`,
`types.ts`) are re-formatted copies of the identically-named source files
shipped in `@oh-my-pi/hashline@16.2.13/src/`. The only deliberate
differences are:

1. Formatter output (Biome vs. the upstream project's Biome config —
   single vs. double quotes, arrow-function paren style, tab vs. two-
   space indent).
2. `NodeFilesystem.readText`, `NodeFilesystem.writeText`,
   `NodeFilesystem.delete`, and the FNV-1a fallback in
   `computeFileHash` are re-expressed against `node:fs/promises` and
   pure-JS `Math.imul` so the vendored core has no direct dependency
   on the `Bun.*` runtime globals for basic FS ops. This preserves the
   contract; it does not add or remove any behavior of the applier.

If you find a divergence outside those two items, please report it via
this repository's issue tracker; the intent is for the vendored core to
track upstream `@oh-my-pi/hashline` closely.

**Terms.** MIT, as declared in the upstream package manifest
(`node_modules/@oh-my-pi/hashline/package.json` → `"license": "MIT"`,
`"author": "Can Boluk"`, `"repository": "git+https://github.com/can1357/oh-my-pi.git"`,
subdirectory `packages/hashline`). At the version audited
(`16.2.13`) the upstream tarball does not include a standalone `LICENSE`
file inside the `@oh-my-pi/hashline` subtree; the manifest-declared
license is authoritative for downstream redistribution.

The standard MIT text applies:

```
MIT License

Copyright (c) Can Boluk and the oh-my-pi contributors

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
```

If Can Boluk or the oh-my-pi maintainers publish a canonical LICENSE
file for `@oh-my-pi/hashline` upstream, this block should be replaced
with that verbatim text.

## `dependencies` — pinned runtime dependencies

Full license text ships with each dependency inside `node_modules/`; the
list here is a summary of what the resolved `bun.lock` pulls at
publication of this repository.

- `diff@9.0.0` — BSD-3-Clause (Kevin Decker).
- `lru-cache@11.5.1` — ISC (Isaac Z. Schlueter and contributors).
- `typebox@1.1.38` — MIT (`sinclairzx81`). Note: this is the standalone
  `typebox` package, not `@sinclair/typebox`.

## `peerDependencies`

- `@earendil-works/pi-coding-agent` (>=0.80.0) — separately installed by
  the Pi host; not redistributed by this repository.
