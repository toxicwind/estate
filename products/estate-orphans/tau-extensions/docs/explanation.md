# Design notes: why hashline-pi looks like this

The tradeoffs behind the shape of the tool. For a walkthrough see
`tutorial.md`, for task recipes see `how-to.md`, and for the grammar
see `reference.md`.

## Why line-anchored patches instead of unified diff

LLMs, unlike humans authoring diffs, work from short windows of the
file at a time. Two failure modes dominate the literature:

- **Context drift.** The model transcribes context lines (` foo`) or
  removal lines (`-old`) that don't match the current file, and the
  patch either refuses to apply or (worse) applies at the wrong hunk
  when a fuzzy applier "helps" by matching a similar-looking region.
- **Stale reads.** The model reads a file, plans an edit, does
  something else, then eventually issues the patch — but the file has
  changed since. A unified diff has no way to signal "this patch was
  authored against a specific version."

Hashline addresses both by design:

1. There are no `-old` rows and no context lines. A section says
   "replace original lines N.=M with this body," and the body is only
   the new content. There is nothing for the model to transcribe
   incorrectly.
2. Every section carries a 4-hex `#TAG` fingerprint of the file the
   section was authored against. The applier refuses to touch a file
   whose current content hashes to a different tag, with a clear
   "re-read" instruction. There is no fuzzy-match escape hatch.

The cost is that the model has to include a tag on every section (mild
prompt overhead) and must re-read after every edit (numbering shifts).
The benefit is that stale-anchor drift never lands.

## What "4-hex tag" costs and buys

The tag is 16 bits. At random-oracle assumption, two independent files
with different content collide with probability 1/65536. That is the
number to keep in mind.

- **Within a single Pi session** the snapshot store holds tags per
  canonical path. Two DIFFERENT files can share a tag (birthday
  problem: expected first collision at ~256 files), but the store
  keys by path, so a shared tag does not confuse "which file is
  which."
- **Within a single section** the tag is compared against the current
  content of the SAME path only. A hash collision between the old and
  new content on that path lets a stale patch land — probability
  1/65536 per patch, per path. The tag is not a MAC; it does not
  defend against a motivated adversary computing a preimage.
  Combined with the seen-line guard (a hunk anchored on a line the
  read never displayed is refused), the real hit rate is much lower.

The reason we don't use a longer tag: it ships in the header of every
section the model authors. A 4-hex tag is trivial for the model to
transcribe from a `read` result; 16 hex characters (a full 64-bit
prefix) more than doubles the token cost of the header for a
protection that already dwarfs the model's actual authorship error
rate. The point is drift detection, not cryptographic integrity.

Mitigation for the 1/65536 case:

- Always re-`read` after a rejected patch — the fresh tag on the read
  result is what the next section should carry.
- On any surprising apply result (blank body, no-op reported, or edit
  landed on the wrong-looking line), stop and re-`read`. The seen-
  line guard catches the common "I remembered a line" failure mode;
  it does not catch a genuine tag collision.
- For high-stakes files (secrets, config that gates production),
  consider prepending `write`-tool creation and skipping `hashline`
  entirely.

## Preflight vs commit: where atomicity actually stops

The README calls the multi-file guarantee "all-or-nothing at
preflight." That's precise but slippery — atomicity has an exact
boundary.

**Before preflight ends** (i.e. before any write hits disk), the
guarantee is total: parse errors, stale tags, missing anchor lines,
overlapping ranges on the same file, and jail escapes all abort the
whole batch. No file changes. This is what most LLM-authored patches
actually get.

**After preflight ends**, the commit loop writes sections one at a
time in patch order. If write N-1 succeeded and write N fails (disk
full, ENOSPC, permission changed mid-batch, or the extension crashed
between writes), sections 1..N-1 are already on disk and sections N+1
onwards were never attempted. The extension surfaces exactly which
sections landed and which did not; it does NOT roll back the landed
ones.

The reason:

- Rolling back would require capturing the pre-edit contents of every
  file the batch touches and then re-writing them on failure. That
  turns an N-section commit into 2N writes even in the happy path.
- It also requires deciding what to do if the rollback itself fails —
  now you have a partially-applied batch AND a partially-rolled-back
  restore. Multi-level partial state is worse than a clearly-reported
  partial commit.
- The set of failures that get you past preflight is genuinely narrow:
  ENOSPC, EIO, permissions mid-batch, or a `MV DEST` collision. All
  of them are recoverable by re-issuing only the missing sections
  against a fresh `read`.

The practical rule: **a patch you're not comfortable seeing in a
half-applied state should be a single section**. If you're doing a
refactor that requires files A, B, C to all change together, split it
into three patches with a `read` between each, or accept that partial
commit reporting is your rollback plan.

## Why the shipped extension jails writes and the vendored core does not

The vendored `NodeFilesystem` in `src/vendor/fs.ts` is a generic seam.
Every file backend has a different sandboxing story — a Git-tree
backend already jails to the tree, an S3 backend jails to a bucket
prefix, a VFS overlay applies its own policy. Baking a `cwd`-based
jail into the seam would either force every backend to bypass it or
force the seam to grow a policy config that no non-Node backend
actually uses.

Instead the vendored core states its contract clearly ("callers
responsible for any cwd or jail/sandbox resolution should wrap this
with their own subclass") and ships an in-memory subclass and a raw
disk subclass. The Pi extension is a caller and takes the "wrap it"
path: `extensions/pi/jail.ts` subclasses `NodeFilesystem` and enforces
the workspace jail. That layering has the following advantages:

- The generic seam stays reusable for backends where a `cwd` jail is
  meaningless.
- The security policy that actually ships is testable in isolation
  (`test/jail.test.ts` targets `JailedNodeFilesystem` specifically,
  not the whole patcher through the seam).
- A future backend — say, an in-memory FS for a chat-based Pi client
  — can pick a different policy without patching the core.

The one wart of this layering is that a naive reader looks at
`src/vendor/fs.ts` and sees an unsandboxed FS class, then panics.
`test/hashline.test.ts` explicitly documents "the core FS abstraction
does not sandbox" to prevent that panic from turning into a bogus bug
report. `SECURITY.md` re-states the same thing: the shipped extension
does not use `NodeFilesystem` directly, and `JailedNodeFilesystem` IS
the security boundary. Read the two together.

## Why block ops parse but don't apply

`SWAP.BLK`, `DEL.BLK`, and `INS.BLK.POST` are in the grammar for
forward compatibility with a future extension that wires a tree-sitter
resolver. Shipping the grammar today keeps existing patches
authored-then-parked-then-replayed forward-compatible — the parser
never has to reject a syntactically-correct patch on a version bump.

In v1 the three variants split three ways:

- `SWAP.BLK` and `DEL.BLK` **hard-fail** with an error that names the
  exact concrete-range fallback (`SWAP N.=M` / `DEL N.=M`). Guessing
  a block boundary from a line-only signal is inherently unsafe:
  Markdown headings, Python indentation, TypeScript trailing commas
  all have off-by-one traps that depend on context we don't have.
- `INS.BLK.POST` **lowers to plain `INS.POST N:` with a warning**.
  This is a compatibility affordance: `INS.BLK.POST N` and `INS.POST
  N` land the same body when the "block that begins on line N" is a
  single-line construct. When it's a multi-line block, they diverge
  (the block variant would land after the closing line, the plain
  variant lands after line N itself). The warning is what asks the
  author to verify. This lowering was ranked "less bad than hard-
  failing all three" — pure inserts are the common case and a
  warning-driven lowering keeps them working.

If you want the block variants to actually resolve syntactic blocks,
wire a `blockResolver` on `Patcher` (see the constructor). The
`prompt.md` will need a corresponding v1 caveat removed and the
adversarial test suite will need cases for the new resolver's
behavior on split decorators, doc-comments, and Markdown headings.

## Why the CI gate is a check, not a publish

This repository is `"private": true` and distributed by clone. There
is no `bun publish` step, no versioned tarball on npm. The CI gate
(`.github/workflows/check.yml`) exists to verify that a change did not
break consumers who install by SHA, not to gate a publish that will
never happen.

The rationale is that the extension's install surface is small (one
repo, one entry point, one FS jail) and its consumer surface is
bounded (Pi extension embedders + one upstream vendored dependency).
Adding an npm publish would introduce a package-name squat risk, a
supply-chain surface, and a semver expectation that the `0.x` API
churn does not warrant. If enough consumers ask for a versioned
release, the right move is a git tag + release artifact, not npm.
