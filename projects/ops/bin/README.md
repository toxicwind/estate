# projects/ops/bin/

Permanent operations scripts for the fleet. Runnable by anyone, anytime, on
yote (CachyOS). The script is the deliverable; a one-off run is just proof.

| Script | What |
|---|---|
| `sudo-audit.sh` | Verifies the pack's action posture: passwordless sudo scope, key paths + permissions, shared-tree ownership (`/home/toxic/sovereign`, `/home/toxic/.tau`), pitchfork/systemd daemon management without interactive auth. Reports blockers; exit 1 if any. `--json` for machine output. |
| `missing-files.sh` | Finds files the system REFERENCES but that don't exist: greps systemd units (Exec*/EnvironmentFile/WorkingDirectory), live configs (`herd.yaml`, `pitchfork.toml`, `ports.env`, …), and docs (`*.md`) for paths, then checks each exists. Prints `MISSING <path>` with the referencing file, line number, and line. `--units` / `--configs` / `--docs` / `--quiet`. |

Related docs:
- Estate map, crews, repo index, standing rules: [`docs/fleet-knowledgebase.md`](../../docs/fleet-knowledgebase.md)
- Hardware audit schema (consumed by `hw-audit.service`): [`docs/HARDWARE_AUDIT_20260914.md`](../../docs/HARDWARE_AUDIT_20260914.md)
- hw-audit masters: [`../yote/ops/hw-audit/`](../yote/ops/hw-audit/)
- Master README: [`../../README.md`](../../README.md)
