# PostgreSQL Ownership — Decision (2026-09-14)

## Status: DOCUMENTED, migration pending a maintenance window

PostgreSQL runs on awrawr-pc as a raw systemd service (`postgresql.service`,
`/usr/bin/postgres -D /var/lib/postgres/data`, active since 2026-08-28). It is
**not** managed by pitchfork/mise, which own the rest of the sovereign stack.

## Standing rule

No dual init systems on awrawr-pc: mise + pitchfork own user toxic's services.
Anomalous non-CachyOS-default systemd units get migrated into the sovereign
pitchfork definitions, then the raw unit is disabled. **Never run both the
systemd unit and a pitchfork daemon for PostgreSQL at the same time.**

## Migration plan (not yet executed)

1. Add a pitchfork daemon (e.g. `postgres`) to the unified service registry:
   - `run = "exec /usr/bin/postgres -D /var/lib/postgres/data"`
   - runs as the `postgres` user, reusing the existing data directory
   - `ready_cmd` on the PostgreSQL port (5432) via `ss`
   - `group = "core"` (infrastructure, no mesh dependency)
2. Regenerate `pitchfork.toml` and verify the new daemon starts and passes
   its readiness check against the live data directory.
3. Only after the pitchfork daemon is healthy: `sudo systemctl disable --now
   postgresql.service` and confirm the raw unit stays down across a reboot.
4. Keep a filesystem-level backup of `/var/lib/postgres/data` before the cutover.

## Why not yet done

The database holds live data and the cutover needs a quiet moment plus a
verified backup. Documented here so the next maintenance window can execute
it; the mesh bruteforce of 2026-09-14 deliberately did not touch it to avoid
risking data loss during the coordinated restart.
