# phone-backup

Bulk backup + storage triage for Chris's Pixel 9 Pro XL, via ADB on yote.
Code, archives, repos, docs — **photos explicitly out of scope** (standing direction).

## The one-liner

```bash
./bin/fast-pull.sh /mnt/8TB/phone-archive
```

4-way parallel `adb pull` across the top-level source dirs. Benchmarked
2026-09-30: ~30 MB/s wireless (vs ~7 MB/s for the tar-stream trick — don't
"go optimize" it back without re-running `bin/speed-race.sh`).

## Layout

| Path | What |
|---|---|
| `bin/fast-pull.sh` | bootstrap parallel pull → `/mnt/8TB/phone-archive`, writes a manifest |
| `bin/speed-race.sh` | 8-method transfer shootout (small-file torture + 300MB blob) |
| `SKILL.md` | the full playbook: storage map, toybox quirk, archive layout, Syncthing verdict |

## Archive

Raw pulls land in `/mnt/8TB/phone-archive/` (26G on 2026-09-30, 7/7 dirs OK).
Triage into `repos/` `archives/` `code/` `docs/` per the skill, then route
reusable work to sovereign or a standalone project folder.

## Future

Batch pulls are the bootstrap. The steady state is **Syncthing phone →
yote/8TB continuous sync**, event-driven on arrival (see SKILL.md §5).
