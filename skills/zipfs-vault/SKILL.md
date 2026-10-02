---
name: "zipfs-vault"
description: "Obfuscated zipfs repo on Google Drive: blobs with random names inside one zip, synced to a Drive folder. Use when content must never be served from a public endpoint but readers are authenticated (e.g. the Squawk fleet-chat feed)."
---

# zipfs-vault

Adapted from `encrypted-github-fs`. One zip is the repo (`store/vault.zip`):
inside it, entries live as `blobs/<random hex>` plus a `manifest.json`
mapping aliases to blob names. The zip syncs to the Google Drive folder
`zipfs` (configurable via `ZIPFS_DRIVE_FOLDER`).

Security model: **obfuscation + authenticated access, NOT encryption.**
Anyone who can read the Drive folder (or the local zip) can unzip it. The
boundary is Google authentication — nothing here is ever served from a
public URL. Do not use it for secrets that must survive Drive compromise;
those go to the encrypted-github-fs vault route.

## CLI

```
./runner.sh init                          # local zip + Drive folder, prints ids
./runner.sh put <file> -a <alias>         # add entry (alias like fleet/000123)
./runner.sh put --text "..." -a <alias>   # inline text entry
./runner.sh get <alias> [-o out]          # fetch entry (stdout default)
./runner.sh list [--json]                 # aliases
./runner.sh rm <alias>                    # delete entry
./runner.sh sync [--via gws|rclone]       # upload local zip -> Drive
./runner.sh pull [--via gws|rclone] [--force]  # download Drive zip -> local (skips if unchanged)
```

Transports: `gws` (default, `$ZIPFS_VIA`) uses the hatch gws CLI (this
cell); `rclone` uses `$ZIPFS_RCLONE_DEST` (default
`gdrive:/zipfs/vault.zip`) — for awrawr-pc, which has rclone but no gws.
Both read/write the same Drive file.

## Chat-feed wiring (Squawk)

- Writer (awrawr-pc, single): relay side appends each new fleet message as
  `put --text '<json>' -a fleet/<seq>` then `sync`. Local zip persists on
  awrawr-pc; Drive holds the online copy.
- Reader (this cell): the `squawk-feed` hook runs `pull` (no-op when
  unchanged), diffs the manifest against its cursor, emits new messages.
- Last-writer-wins: never have two writers `put`+`sync` without a `pull`
  in between.

## Operating rules

1. The zip is the unit of sync; `pull` before `put` if another writer may
   have synced since your last pull.
2. Blob names are random per put — re-putting the same alias replaces the
   blob and drops the old one.
3. `store/` holds the local zip + `drive.json` (folder/file id cache). It is
   machine-local state, never committed.
