# projects/ops — estate operations tooling

Durable, committed home for operations scripts that used to live as /tmp
scratch, one-off bridge commands, or hand-applied patches.

- `bin/monkeypatch-detect.sh` — hunts non-durable fixes across the estate:
  /tmp scripts doing production jobs, shell exports that belong in real
  config, hand-started daemons with no unit, patched files outside any repo
  (node_modules patches), symlinks into /tmp. Reports each with a suggested
  durable home. Exit 1 on findings, 0 when clean. Read-only — never
  modifies, kills, or restarts anything. Run anytime:
  `projects/ops/bin/monkeypatch-detect.sh`

- `bin/fleet-health.sh` — one-shot fleet channel health audit: flags
  stuck/silent/dead agents (joined but never reported), erroring loops, and
  watchdog template-spam. Exit 1 on findings, 0 when clean. The deliverable;
  a health pass is just its first run. Run anytime:
  `projects/ops/bin/fleet-health.sh [--hours 24]`

Standing rules (Chris, 2026-09-20): **no monkeypatching, permanence rule.**
Every fix lives in real files — code, configs, systemd units — committed
in the correct repo, and must survive a full bridge restart and a full
yote reboot. The script is the deliverable; running it once is just proof.

See the repo master README for the estate map.
