# pack-fix

Orphan-hunting crew: find orphaned stuff on yote and the cell — adopt it or clean it.
Never leave a reorg half-done.

- Lane (per Chris): **yote processes only** — process inventory vs known daemons,
  stale pid files. `/tmp` file triage → kimi-unlock-audit; repo orphan
  integration → repo-integrator-max.
- [bin/orphan-sweep.sh](bin/orphan-sweep.sh) — permanent repeatable process-orphan
  audit. Report-only; disposition (adopt/kill) is announced in the fleet channel.
- [orphan-sweep.md](orphan-sweep.md) — evidence log of the 2026-09-20 sweep.

Docs: [sovereign docs](../../docs/) · [master README](../../README.md) ·
[fleet knowledgebase](../../docs/fleet-knowledgebase.md)
