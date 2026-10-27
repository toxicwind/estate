# Security policy

## Reporting a vulnerability

If you believe you have found a security-relevant bug in `hashline-pi`,
please **do not open a public issue**. Instead, use GitHub's private
security advisory workflow on this repository:

- Advisory form: <https://github.com/acoyfellow/hashline-pi/security/advisories/new>

If for any reason you cannot use GitHub's advisory workflow, open a
minimal public issue asking the maintainer to contact you off-issue and
supply an out-of-band channel — do not paste exploit details into the
public issue itself.

You should get an acknowledgment within a few working days. Once a fix
is ready we will coordinate a disclosure window with you before
publishing release notes.

## Scope

The extension executes as part of the Pi coding agent, which has its own
security posture. In-scope issues for **this** repository include:

- A malicious patch input that escapes the workspace jail (writes,
  deletes, or moves against a path whose lexical resolution or
  symlink-resolved realpath sits outside the extension's root).
- A malicious patch input that causes the extension to hang, crash, or
  consume unbounded memory.
- A parse-time flaw that lets a section apply against the wrong file
  despite the snapshot tag.
- A jail-bypass via any code path in `extensions/pi/` — including tag-
  based path recovery, `MV DEST`, `REM`, absolute-path headers, or
  symlinks planted inside the root.

Out of scope:

- The generic `NodeFilesystem` seam in `src/vendor/fs.ts`. It is
  intentionally not sandboxed and is not what this extension ships
  wired to `Patcher`. `test/hashline.test.ts` explicitly documents that
  the seam allows out-of-root writes; that is a property of the seam,
  not a bug. The shipped extension wraps it with `JailedNodeFilesystem`.
- Anything requiring the attacker to already have arbitrary write
  ability as the Pi user; the extension is not a sandbox around
  attacker-controlled shells.
- General Pi agent behaviors — please report those to the Pi project.

## What "workspace jail" means

The shipped extension (`extensions/pi/index.ts`) constructs a
`JailedNodeFilesystem` rooted at `process.cwd()` at init time. Every
path the model authors — section headers, `MV DEST`, tag-based path-
recovery targets — is:

1. Resolved lexically against the root; absolute paths outside the
   root and `..` traversals that escape are rejected before any
   filesystem call runs.
2. Realpath-checked before any write, so a symlink inside the root
   pointing to an out-of-root file or directory cannot smuggle a
   write out.
3. Refused for tag-based path recovery to any out-of-root canonical
   path.

The jail is enforced with `JailEscapeError`, which is thrown from
`canonicalPath` (sync), `preflightWrite`, `writeText`, `delete`, and
`move`. The portable Node implementation performs a realpath check before
the write; it cannot eliminate the classic check-to-use race if another
process with the same user's write privileges swaps a directory for a
symlink between those operations. That attacker capability is outside the
threat model above. See `test/jail.test.ts` for the exhaustive matrix of
what is refused and what is accepted.

## Supported versions

While the package is at `0.x` only the latest `main` branch is
supported. Point your Pi installation at a tagged GitHub release or a
specific commit SHA if you need reproducibility.
