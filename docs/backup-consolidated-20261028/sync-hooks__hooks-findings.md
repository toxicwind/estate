# hooks-findings.md — hook mechanism spike (general, purpose-agnostic)

**Status:** COMPLETE 2026-09-15 ~03:45 UTC — harness `/home/toxic/hook-spike-20260915/`,
full report `REPORT.md` there, evidence pushed to `toxicwind/hook-spike-20260915`.
**Task:** maximally test how to add hooks to (a) `~/.bashrc` (interactive shells) and
(b) the fleet job runner (`/home/toxic/fleet/jobs/bin/job`). Testing only — no live changes.

## Intake from research-needs.md (read 2026-09-15 ~03:36 UTC)
Research side needs, in priority order: (1) read-only on-demand pty traffic tap with
verbatim ESC bytes, ≤50MB rotation, 0600; (2) env snapshot at shell startup incl.
`WEZTERM_*`, working in login shells without `/etc/profile.d`; (3) event timestamps;
(4) same for runner/non-interactive shells. Secrets hygiene: 0600, never commit captures.

## 🏆 WINNING MECHANISM (flagged for adoption)
A kit, one mechanism per context — all tested, all in `/home/toxic/hook-spike-20260915/hooks/`:
- **Interactive bash:** `common.sh` — dual-mode fragment sourced from `~/.bashrc`;
  installs `PROMPT_COMMAND` (precmd) + `DEBUG` trap (preexec), idempotent, chain-preserving.
- **Runner bash jobs:** same `common.sh` via `BASH_ENV` in the spec env (zero runner changes).
- **Runner any-language jobs:** native `pre.d`/`post.d` hooks — patch `_jobwrap.py`
  (`results/runner-hook-patch.diff`); pre-fail → `hook_failed` + body skipped,
  post-fail → logged to `wrapper.err`, status preserved.
- **Traffic tap:** `ptap.sh` — on-demand `script(1)` pty wrapper; verbatim ESC bytes,
  rc propagation, rotation, 0600. Satisfies every hard requirement in research-needs.md.
- **Env snapshot:** `envsnap.sh` (0600), `TERM/COLORTERM/TERM_PROGRAM/BASH_ENV/PATH/PAGER/LESS/WEZTERM_*`.

## Measured overhead (per-invocation, HFT framing)
- `PROMPT_COMMAND` hook body: **~5 µs**/prompt (below noise floor in-pty).
- `DEBUG` trap hook body: **~39 µs**/simple command — the only non-trivial tax; it fires
  per command incl. loops, so keep the body minimal.
- `common.sh` source / `BASH_ENV` one-shot: sub-ms.
- Runner native hook: **~0.75 ms**/hook spawn.
- `ptap`: **~24 ms**/tapped invocation (one-shot, not per-prompt).

## Key behavioral findings
- `PROMPT_COMMAND` does **NOT** fire under `bash -i -c` (clean-HOME verified; an early
  contaminated run false-positived — corrected). Non-interactive jobs must use `BASH_ENV`/native.
- `DEBUG` trap **does** fire in non-interactive `bash -c` — the only shell-native
  hook that works without `-i`.
- Appended `PROMPT_COMMAND` hook sees the *previous element's* `$?`, not the command's
  (verified: `false` → hook saw rc=0). If exit codes matter, hook goes first.
- Failing hooks never kill the shell: PCMD `return 1` doesn't clobber `$?` (verified
  `GOT_RC=1`); failing DEBUG trap doesn't suppress the command (verified `CMD_RAN`).
- Login shells ride the `.bash_profile → .bashrc` chain (verified) — no `/etc/profile.d` needed.
- All fragments idempotent under double-source; existing PROMPT_COMMAND/DEBUG traps chained.

## Failure modes
- Hook exits nonzero → shell survives; runner pre-hook → `hook_failed` (body skipped),
  post-hook → logged, status kept.
- `FLEET_MARKERS` unset → `common.sh` defaults to `/dev/null` (never breaks a shell).
- Missing hook dir → silently skipped. Hook stdout → pre-prompt, harmless.

## Insertion snippets
`~/.bashrc` (after existing prompt/trap setup):
```bash
# --- fleet hooks (managed block) ---
if [[ -r "$HOME/.fleet-hooks/common.sh" ]]; then
  # shellcheck source=/dev/null
  source "$HOME/.fleet-hooks/common.sh"
fi
# --- end fleet hooks ---
```
Runner bash jobs: `"env": { "BASH_ENV": "/home/toxic/.fleet-hooks/common.sh" }`.
Runner native: apply `results/runner-hook-patch.diff`, set `spec["hook_dir"]`.
Traffic tap: `ptap.sh [--log FILE] -- <cmd> [args...]`.

## What the research side gets
Adopt `common.sh` + `envsnap.sh` + `ptap.sh` as-is for the captures in research-needs.md
(per-command timing/markers, env snapshots, read-only pty tap). No new mechanism needed.
