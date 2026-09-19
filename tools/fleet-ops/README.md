# fleet-ops — hatch cell saturation patches (debate 2c7ca733)

Built 2026-09-19 after the iowait-freeze incident (50–80% iowait, load 10–13
on 2 cores, caused by orphaned recursive greps over ~/workspace).

| script | purpose |
|---|---|
| `safe-rg` | wrapper: refuses unscoped `rg` over ~/workspace (exit 2); scoped searches get timeout + idle ionice; `--yolo` override stays capped |
| `orphan-reaper` | dry-run by default; `--kill` reaps PPID-1 `rg`/`grep`/`find` older than 300s touching ~/workspace |
| `io-rate-reaper` | kills by measured `/proc/PID/io` read rate (>100MB/s sustained), not just orphan status; honors `io-lease` |
| `iowait-gate` | exit 0 when iowait < 40%, exit 1 when saturated — heavy jobs defer on 1 |
| `io-lease` | `io-lease --ttl 600 --reason TEXT` — declares forensics work so reapers skip it (answers lane-4's con seq 6 point 2) |
| `oracle-judge` | debate-oracle scaffolding: renders judge-brief, checks pro+con+synthesis readiness, prints the judging rubric + resolve invocation |

Also mirrored to `/home/toxic/.local/bin/` (on PATH). Runtime state
(`safe-rg.log`, `.io-leases/`) is NOT committed.
