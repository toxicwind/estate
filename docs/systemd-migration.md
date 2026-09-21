# systemd substrate migration contract

**Status:** proof of concept (P3 of the supervision paper fixes, DESIGN.md).
Migrated: `forensics-srv` only (2026-09-20). This is NOT a fleet migration —
the other 67 daemons remain pitchfork-supervised until P1 (reconciler) has
stabilized the fleet.

## Contract

1. **pitchfork.toml stays the human source of truth.** Run lines, dirs, and
   env blocks are edited in the toml only.
2. **The exporter regenerates units on toml change.** `bin/pitchfork-export-systemd
   --daemon <name>` (or `--all`) writes `~/.config/systemd/user/sovereign-<name>.service`,
   then `systemctl --user daemon-reload`. Units are generated, never hand-edited.
3. **pitchfork remains the status layer during transition.** A migrated daemon's
   pitchfork registration is kept but STOPPED (dual state, declared honestly):
   `pitchfork status` shows `stopped`; systemd is the source of truth for the
   process (`systemctl --user status sovereign-<name>`). Do not `pitchfork start`
   a migrated daemon — that would double-bind its port.
4. **Migrate incrementally, highest-churn first, one at a time.** Each migration
   is verified (serves + survives `restart` + survives stop/start) before the
   next begins. ANY instability → roll back to pitchfork, document, stop.
5. **Never migrate:** squawk-ws/squawk-feed (fleet comms), awrawr-ws-exec
   (live bridge), herd, keypool, model-guard, or `mise = true` daemons until
   PATH pinning is solved (pitchfork injects mise shims; systemd does not).

## Unit shape (generated)

`Type=simple`, `Restart=always`, `RestartSec=5`, `WorkingDirectory=<dir>`,
`Environment=` lines from the env block (systemd-quoted), `ExecStart=<run
minus leading 'exec '>`, `WantedBy=default.target`, logging to journald.
`loginctl show-user toxic` → `Linger=yes` (already enabled; required for
reboot persistence of user units).

## Migration ledger

| daemon | migrated | pitchfork state | systemd state | verified |
|---|---|---|---|---|
| forensics-srv | 2026-09-20 | stopped (registration kept) | `sovereign-forensics-srv.service` active, :25160/health | restart OK, stop/start cycle OK, NRestarts=0 |

Chosen as PoC: highest supervisor churn in 7d (retry_count=31 in state.toml,
mostly the post-reboot EADDRINUSE storm), self-contained venv, real HTTP
health probe (`curl -sf http://127.0.0.1:25160/health`), no env, no secrets.

## Rollback procedure (per daemon)

```sh
systemctl --user stop sovereign-<name>.service
systemctl --user disable sovereign-<name>.service   # keep the unit file for forensics
cd /home/toxic/sovereign && pitchfork start <project>/<name>
# verify via the daemon's ready probe
```

## Re-migration after rollback

Fix the root cause in the toml (the bug is almost always there, not in the
unit), regenerate with the exporter, and re-run the verification gauntlet:
`start` → ready probe → `restart` → ready probe → `stop` → port free → `start`
→ ready probe → confirm NRestarts=0.
