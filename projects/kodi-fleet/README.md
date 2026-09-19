# kodi-fleet

One-shot Kodi tooling + audit for the two-box fleet. Lives in the sovereign repo;
runs from awrawr-pc (has the LAN route + SSH).

## Boxes

| box | host | platform | access |
|-----|------|----------|--------|
| 246 | 10.0.0.246 | CoreELEC (living room) | SSH `root:coreelec`, JSON-RPC :8080 (no auth) |
| 225 | 10.0.0.225 | Android / Google TV (bedroom) | JSON-RPC :8080 only (no SSH) |

Reference box is **246** ("it has correct"). Dupes go 246 -> 225, except
tv/audio settings, which stay per-box.

## Tools (`bin/`)

- **kodi-handoff** — one-shot playback transfer: `kodi-handoff <src> <dst> [--play]`.
  Freezes source, opens the same stream URL on the destination, waits for a real
  duration, retries seek to <1%, leaves dst paused (or playing with `--play`).
  Test without disturbing playback: `kodi-handoff --dry-run <src> <dst>` and
  `kodi-handoff --selftest <ip>` (no-op seek, 0.00% drift).
- **kodi-audit** — fleet audit:
  - `latency [246|225|all]` — JSON-RPC round-trip stats (10x Ping)
  - `addons [--diff]` — inventory + 246/225 diff (report-only by design)
  - `settings [--diff]` — settings dump diff
  - `settings --dupe` — copy 246 -> 225 for the safe allowlist only
  - `logerrors 246` / `stalls 246` — 246's kodi.log via SSH

Deployed copies: `/home/toxic/bin/kodi-handoff` (symlink or copy of `bin/` source).
Keep the repo source canonical; re-deploy after edits.

## Docs (`docs/`)

- `menu-latency.md` — UI-sluggishness diagnosis (both boxes)
- `box-inventory.md` — hardware/platform/filesystem notes

## Kodi JSON-RPC gotchas (learned live)

- `Player.Seek` value must be a wrapped object: `{"value": {"percentage": x}}`.
  Bare numbers and raw time objects are rejected (-32602).
- `Player.GetItem` has no `label` field on Kodi 21 — request `file`, `title`.
- First seek after `Player.Open` often lands ~0%: retry until within 1%.
- `Player.Seek` can throw -32100 during transitions: retry on RPC error.
- Re-fetch the video playerid after open; never assume 1.
