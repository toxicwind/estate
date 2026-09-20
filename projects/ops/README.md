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

- `bin/bg-launch`, `bin/bg-register`, `bin/bg-heartbeat`, `bin/bg-audit`,
  `bin/bg-kill` + `bg-tracker/` — **bg-tracker**: the background-task
  registry. Every detached job launches (or retro-registers) through it;
  who/what/why/pid recorded in a durable per-box registry
  (`bg-tracker/state/`, gitignored runtime state). `bg-audit` is read-only:
  classifies every detached proc (KNOWN-SYSTEM / SUPERVISED /
  REGISTERED-OK / REGISTERED-STALE / REGISTERED-DEAD / UNREGISTERED /
  AMP-VICTIM), exit 1 when anything needs attention, never kills.
  Event-driven — no polling daemons. Full docs: `bg-tracker/README.md`.
  Kill policy: positive orphan confirmation + fleet evidence note at kill
  time; when in doubt, leave running and flag.

See the repo master README for the estate map, and
`docs/fleet-knowledgebase.md` §2 for the crew registry.
