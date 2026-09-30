# warden-restore-kill

**Scope:** Disable ALL estate-reconcile restore paths — autonomous watch AND manual `--apply` — alert-only everywhere (Chris 2026-09-30: ferrous warden should not restore anything).
**Owner / coordinator:** ashen (Ember's crew)
**Status:** RUNNING

## Work
- `bin/estate-reconcile`: `cmd_apply` replaced with fail-closed refuse stub (exit 2, logs APPLY-REFUSED); `_restore_from_copy` / `_restore_from_git` neutered to refuse stubs; `_backup_drifted` removed; zero restore mechanics remain.
- `bin/tests/estate-reconcile-test.sh`: restore-positive tests rewritten as refusal tests (15/15 pass).
- `deploy/manifest.yaml`: restore-rules comment block replaced with HARD-DISABLED notice.
- `bin/herd-keypool.py`: stale `estate-reconcile --apply` hint replaced with alert-only notice.
- `projects/herd/FALLBACK.md`: warden-path restore doc updated to HARD-DISABLED.
- Watch loop was already alert-only (2e270e971d); breaker message corrected.

## Done criteria
- Commit on toxicwind/sovereign-projects main, remote ref verified.
- estate-reconcile-watch daemon restarted on the new build; `--apply` refuses live.
