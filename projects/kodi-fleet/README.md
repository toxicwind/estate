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
- **kodi-resume** — cross-box playback resume ("continue in the other room").
  Kodi only keeps resume bookmarks for library items, but both fleet boxes
  stream mostly via addons (empty video libraries), so resume dies at the
  door. `kodi-resume` keeps a tiny state file on awrawr-pc instead:
  - `record` — snapshot active players on 246+225 (read-only; 30s minimum,
    dedupes same stream within 60s)
  - `status` — list saved sessions (box, title, position, age)
  - `continue <246|225> [--apply] [--play]` — open the newest session from
    the *other* box at the exact saved position; defaults to `--dry-run`
    (prints the RPCs). Refuses if the target is already playing anything.
  - `prune [--keep N]` — keep newest N sessions (default 20)
  - `--selftest <ip>` — read-only RPC path check
  - 18 unit tests: `python3 -m unittest discover -s tests` (0.07s)
  Live note: `--apply` was validated via dry-run + mocked-RPC tests only —
  a real open+seek was deliberately not fired at 04:35 (sleeping house).
  State: `~/.local/share/kodi-fleet/resume.json` (outside the repo).

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
