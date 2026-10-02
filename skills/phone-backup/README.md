# phone-backup

[![for-the-badge](https://img.shields.io/badge/ADB-0D7377?style=for-the-badge)](https://developer.android.com/studio/command-line/adb) [![for-the-badge](https://img.shields.io/badge/Pixel-9-Pro-XL-FF6F61?style=for-the-badge)](https://google.com/pixel) [![for-the-badge](https://img.shields.io/badge/8TB-phone-archive-FFD700?style=for-the-badge)](https://awrawr-pc)

## phone-backup

Bulk backup and storage triage for Chris's Pixel 9 Pro XL via ADB on yote. Benchmarked fastest pull (parallel adb pull, NOT tar-stream), phone storage map, the toybox find quirk, 8TB archive layout, and the future-forward Syncthing continuous-sync direction. Use when Chris asks about phone storage, pulling files off the phone, or freeing phone space. Photos (DCIM/Pictures) are excluded by standing direction — this skill handles code, archives, repos, and documents only.

### Where things live (do not re-derive)

| Thing | Location |
|---|---|
| ADB binary | `/usr/bin/adb` on yote |
| Phone endpoint | `10.0.0.77:<port>` — **port rotates**; keepalive daemon rediscovers it |
| Keepalive | `sovereign/ranch/android-fleet/bin/pixel-adb-keepalive.sh` (pitchfork) |
| Canonical project | `sovereign/ranch/android-fleet/phone-backup/` |
| Fast pull script | `.../phone-backup/bin/fast-pull.sh` |
| Speed shootout | `.../phone-backup/bin/speed-race.sh` (8 methods, keeps the winner) |
| Archive root | `/mnt/8TB/phone-archive/` (7.3T drive, was 13% used 2026-09-30) |
| Phone sweep scripts | `~/workspace/phone-sweeps/phone_scan.sh`, `phone_content.sh` |

Always resolve the live endpoint first: `adb devices | awk '/^10\.0\.0\.77:[0-9]+[[:space:]]+device/'`. `fast-pull.sh` does this itself if `PIXEL` is stale.

### The toybox quirk (will bite you)

`find /sdcard -type f` returns **nothing** on this phone (toybox). Iterate top-level dirs instead:
```bash
for d in /sdcard/*/; do find "$d" -type f ...; done
```
Same for `du`: per-dir `du -sm /sdcard/*/` works; bare `du -sm /sdcard` may not.

### Fastest pull method (benchmarked 2026-09-30, wireless ADB)

**8-method shootout** (`bin/speed-race.sh`, Pixel 9 Pro XL):

Small files (1000 × 100KB = 131MB):

| Method | Time | Throughput |
|---|---|---|
| on-device `tar` + single pull | 4.5s | ~29 MB/s ← **winner (small files)** |
| 8-way parallel `adb pull` | 6.4s | ~20 MB/s |
| plain `adb pull` | 15.9s | ~8 MB/s |
| `adb pull -z` (compressed) | 14.8s | ~9 MB/s |

Large file (300MB incompressible blob):

| Method | Time | Throughput |
|---|---|---|
| plain `adb pull` | 6.8s | ~44 MB/s ← **winner (large files)** |
| on-device `tar` + pull | 8.0s | ~38 MB/s |
| `adb pull -z` | 7.6s | ~40 MB/s |
| `exec-out cat` pipe | 35.0s | ~9 MB/s (framing overhead kills it) |

**The verdict is HYBRID, not one method:**
- Many small files → `tar` on device first, then pull the single tarball. Eliminates per-file sync-protocol round-trips (the real bottleneck).
- Large files → plain `adb pull`, no tar overhead, max sequential throughput.
- `adb pull -z` never wins on incompressible data; `exec-out` pipes always lose.

```bash
# One-shot, default source set (~20GB code/archives/repos/docs)
/home/toxic/sovereign/ranch/android-fleet/phone-backup/bin/fast-pull.sh /mnt/8TB/phone-archive

# Re-run the 8-method speed shootout
/home/toxic/sovereign/ranch/android-fleet/phone-backup/bin/speed-race.sh ${TMPDIR:-$HOME/.cache}/speed-race
```

Each run writes a timestamped manifest (`pull-manifest-*.txt`) with per-dir OK/FAIL, sizes, and file counts. **Never delete from the phone until the manifest is verified** (spot-check sizes + open a few archives).

2026-09-30 pull result: 26G, 7/7 dirs OK (`Export` 86M, `1openfang` 39M, `Tasker` 16M, `House` 12M, `Documents` 259M, `ik_llama.cpp-main` 112M, `Download` 25G/14925 files).

### Phone storage map (2026-09-30, `du -sm /sdcard/*/`)

| Dir | Size | Action |
|---|---|---|
| `DCIM/` | 71.6G | **photos — ignore** (standing direction) |
| `Download/` | 19.6G | pull → archive (biggest win) |
| `Android/` | 17G | app data — hands off, except safe cache trims |
| `Movies/` | 13.8G | personal media — ask Chris before touching |
| `Pictures/` | 13G | **photos — ignore** |
| `Documents/` | 259M | pull → archive |
| `ik_llama.cpp-main/` | 115M | repo → archive, then decide: sovereign or standalone |
| `Export/`, `1openfang/`, `Tasker/`, `House/` | ~150M | pull → archive |

**Download/ heavies**: `base/` 2.1G, `Unchained/` 1.4G, `YTDLnis/` 905M, `Telegram/` 316M, `Nekogram/` 270M, assorted zips/apks.

### Archive organization

`/mnt/8TB/phone-archive/` receives the raw pull. Then triage:

- `repos/` — git checkouts (e.g. `ik_llama.cpp-main`) → decide sovereign (`sovereign/projects/…`) vs standalone project folder.
- `archives/` — zips/tar.gz/apks, including misnamed ones (`*.tar.gz.pdf`, `*.zip.pdf` — detect by magic bytes, not suffix; see phone-sweeps).
- `code/` — loose scripts, configs, Tasker exports.
- `docs/` — dossiers, reports, saved pages (Chris's research corpus).
- `manifests/` — pull manifests, forever.

### Future-forward: event-driven sync (the debate verdict)

Batch pulls are the bootstrap, not the steady state. GitHub relevance (2026-09-30): `syncthing/syncthing` 89k stars, pushed today — dominant and alive; `rclone/rclone` 60k, alive; `google/adb-sync` archived/dead.

**Verdict: Syncthing phone → yote/8TB continuous sync** is the future-forward lane — files land on the archive as they're created, event-driven, no batch jobs, no timers (matches the estate doctrine). `fast-pull.sh` remains the one-shot/backfill tool. Next build: Syncthing on the Pixel (official Android app) + yote sidecar writing to `/mnt/8TB/phone-archive/incoming/`, with the triage classifier running on arrival.

### Safety rules

- Photos are out of scope, always. Never `adb shell rm` under `DCIM/` or `Pictures/` from this skill's flows.
- The phone is Chris's daily driver: no `pm clear`, no uninstalls, no cache wipes beyond explicit per-app approval.
- Every destructive phone-side step needs a verified manifest first.
- `adb` runs on **yote**, never from the cell (no ADB there).
- **Commit the project dir immediately.** 2026-09-30: the untracked `phone-backup/` tree was wiped from the yote checkout by another lane's cleanup between 03:08 and 03:15 — `fast-pull.sh` and `speed-race.sh` had to be rewritten from scratch. Untracked work in a shared checkout is one `git clean` away from gone. Write → commit → push, same session.