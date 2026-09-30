# Hooksmith — git hooks that don't get in the way

One source of truth for git hooks across the estate. Fast, high-precision,
and allergic to false positives.

## Why the old hooks failed (the audit)

**Old pre-commit** (`sovereign/.git/hooks/pre-commit`, disabled 2026-09-30):

| Check | What it did | Why it hurt |
|---|---|---|
| Lockfile gate | Blocked any commit touching `bun.lock`/`package-lock.json` unless `PI_ALLOW_LOCKFILE_CHANGE=1` | Legitimate dependency updates got blocked; the bypass env var was obscure and undiscoverable |
| Gitleaks, official 222-rule config | `protect --staged` with the default rule set | Flagged test fixtures (`tc:nodekey:0123456789abcdef…` in `*.test.ts`), base64 image/font blobs in SVGs, and example keys. No test-file exclusions, no placeholder allowlist |
| KB freshness | Delegated to another hook script | Noise — unrelated to commit safety |

**Old push-guard** (`bin/push-guard.sh`, 389 lines):

| Check | Why it hurt |
|---|---|
| Same 222-rule gitleaks scan | Same false positives, now blocking *pushes*. Required a manual per-path ignore-memory workflow (`push-guard.sh ignore …`) — human review for every false positive |
| `git diff --check` | Blocked a real push over a blank line at EOF in a `.svelte` file |
| gofmt + go vet | Slow, Go-specific checks in a push hook that also guards the Svelte UI |

Chris's verdict: *"its causing more trouble than intended right now tbh."*

## Design principles

1. **Never block legitimate work.** Test fixtures, example keys, base64 assets,
   and lockfile updates from real dependency changes must NOT be blocked.
2. **Catch real secrets.** Known key formats (`AKIA…`, `ghp_…`, `sk_live_…`,
   `xoxb-…`), PEM private keys, high-entropy assigned values.
3. **Fast.** <100ms for the pre-commit path. One gitleaks invocation, no Go toolchain.
4. **One source of truth.** This directory. Every repo installs from here.
5. **Sane override.** `git commit --no-verify` / `git push --no-verify` always works.
   `HOOKSMITH_SKIP=1` is the loud alternative (prints an audit line).
6. **Warn vs block.** Definite secrets → block. Odd-but-not-secret (lockfile
   changed without its manifest) → warn and continue.

## What's here

| File | Role |
|---|---|
| `pre-commit` | The hook. One gitleaks `protect --staged` scan with `gitleaks.toml` (blocks), plus lockfile advisories (warn). Skips gracefully if gitleaks or the config is missing. |
| `pre-push` | Lighter backstop. Gitleaks `detect --log-opts` over each pushed ref range. Catches `--no-verify` commits and rebases. |
| `gitleaks.toml` | Custom high-precision config. 6 rules (key formats + PEM + generic assignment). Global path allowlist: test files, fixtures, `*.example`, generated assets (svg/png/fonts), lockfiles. The generic rule additionally allowlists placeholder values (`example`, `fake`, `changeme`, repeating patterns like `0123456789abcdef`, `xxx…`). Key-format rules are deliberately strict — a committed `AKIA…` or `ghp_…` is always flagged, even with EXAMPLE in it (GitHub's scanner does the same). |
| `install.sh` | Installer. Usage: `install.sh [repo-path]`. Inside sovereign-projects it symlinks (hooks track the checkout); elsewhere it copies a snapshot (re-run to update). Idempotent. |

## What the hooks deliberately do NOT do

- **No lockfile gate.** The old `PI_ALLOW_LOCKFILE_CHANGE` block is gone. A lockfile
  changing without its manifest prints a one-line note, nothing more.
- **No whitespace gate.** Trailing whitespace / blank-line-at-EOF is an editor
  concern, not a commit blocker.
- **No gofmt / go vet.** Slow, language-specific, and they broke pushes for
  unrelated trees. CI owns formatting.
- **No KB checks.** Unrelated to commit safety.

## Install

```sh
# sovereign-projects (or anywhere, after cloning it):
./tools/git-hooks/install.sh /path/to/repo

# verify:
ls -l /path/to/repo/.git/hooks/pre-commit
```

Repos currently installed: `sovereign-projects`, `ranch`, `herd`.

## Bypass

```sh
git commit --no-verify   # always works, no questions asked
git push --no-verify     # same for pushes
HOOKSMITH_SKIP=1 git commit   # loud alternative: prints an audit line
```

If a *test fixture* trips the scanner, the right fix is to move it into a
`*test*` file or `fixtures/` directory (both excluded) — not to bypass.

## Tuning

- `HOOKSMITH_CONFIG=/path/to/gitleaks.toml` — override the config.
- `GITLEAKS_BIN=/path/to/gitleaks` — override the binary.
- `HOOKSMITH_TIME=1` — print hook timing to stderr.

To add a rule or allowlist entry, edit `gitleaks.toml` here and re-run
`install.sh` in the snapshot repos (ranch, herd). Symlinked repos
(sovereign-projects) pick it up immediately.
