# push-guard secret scan: ignore memory + placeholder auto-clear

`bin/push-guard.sh` (mirrored at `tools/push-guard.sh`) is the pre-push / CI
guard. Check 0 scans added diff lines for secret-shaped tokens. Two valves keep
reviewed files from blocking pushes forever (Chris 2026-09-21: approval is
durable, the guard remembers).

## Ignore memory

- File: `~/.config/push-guard/ignore` (override with `PUSH_GUARD_IGNORE=/path/to/file`).
- Format: one repo-relative path per line; `#` comments and blank lines ignored.
- Matching: exact repo-relative path, or trailing path suffix (`/<entry>` at the
  end of the path), so entries survive repo-root renames.
- Ignored files are never scanned.

Manage it:

- `push-guard.sh ignore <path>...` — remember reviewed paths by hand (run inside
  the repo; this is the safe non-scanning invocation).
- The guard itself appends files whose every secret-shaped token was
  placeholder-shaped (see below).

## Placeholder auto-clear

A file is cleared without blocking when EVERY secret-shaped token in it looks
like a test/example/fake/dummy/redacted/fixture placeholder:

- the token names itself fake (case-insensitive): test, example, sample, fake,
  dummy, placeholder, redacted, fixture, mock, changeme, your_key, xxx;
- or it is structurally fake: one character repeated 6+ times, or a sequential
  run (`0123456789`, `1234567890`, `abcdef`).

Such files are auto-appended to the ignore memory and the auto-clear is logged.

## Still blocks

- Any real-looking token on a non-remembered file refuses the push.
- Bare `BEGIN ... PRIVATE KEY` headers are never auto-cleared: a header alone
  is indistinguishable from a real key's header. Remember the file after review.
- Only file names are ever printed, never matched text.
- The refusal message tells the reviewer the exact remember command.

## Deploying

- Canonical source: `toxicwind/sovereign-projects:bin/push-guard.sh`.
- Live fleet copy: `/home/toxic/bin/push-guard.sh` — Sovereign's hook delegates
  here. Refresh after a repo update with:
  `install -Dm755 <repo-copy> /home/toxic/bin/push-guard.sh`
