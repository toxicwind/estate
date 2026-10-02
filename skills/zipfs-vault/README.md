# zipfs-vault

**Obfuscated zipfs repo on Google Drive** – store blobs with random names inside a single ZIP file, synchronized to a Drive folder, for authenticated-only access (e.g. Squawk fleet-chat feed).

## Why It Matters

When content must never be exposed via public URLs but still needs to be shared among authenticated users (like fleet chat logs), traditional public repositories pose a risk. This skill provides:
- **Obfuscation**: Content is stored as randomly named blobs inside a ZIP, making casual inspection difficult
- **Authentication boundary**: Access relies solely on Google Drive permissions—no public URLs are ever generated
- **Sync efficiency**: Only the ZIP file is transferred, not individual blobs
- **Application-ready**: Designed for use with the Squawk fleet-chat feed and similar internal tools

## What It Does

This skill manages a ZIP-based filesystem where:
- All content lives inside `store/vault.zip` as `blobs/<random hex>` files
- A `manifest.json` inside the ZIP maps human-readable aliases (e.g. `fleet/000123`) to blob names
- The ZIP synchronizes to a Google Drive folder (configurable via `ZIPFS_DRIVE_FOLDER`)
- Access is restricted to those who can read the Drive folder—nothing is ever served from a public endpoint

## CLI Commands

```bash
# Initialize local ZIP and Drive folder (prints IDs for verification)
./runner.sh init

# Add a file entry (alias like fleet/000123)
./runner.sh put <file> -a <alias>

# Add inline text entry
./runner.sh put --text "..." -a <alias>

# Fetch an entry (outputs to stdout by default)
./runner.sh get <alias> [-o out]

# List all aliases (use --json for machine-readable output)
./runner.sh list [--json]

# Delete an entry by alias
./runner.sh rm <alias>

# Upload local ZIP to Drive
./runner.sh sync [--via gws|rclone]

# Download Drive ZIP to local (skips if unchanged)
./runner.sh pull [--via gws|rclone] [--force]
```

## Transports

- **`gws`** (default, `$ZIPFS_VIA`) – uses the hatch gws CLI (available in this cell)
- **`rclone`** – uses `$ZIPFS_RCLONE_DEST` (default `gdrive:/zipfs/vault.zip`)—for awrawr-pc, which has rclone but no gws

Both transports read/write the same Drive file, allowing seamless switching based on available tools.

## Chat-Feed Wiring (Squawk)

The zipfs-vault is wired into the Squawk fleet-chat feed as follows:

1. **Writer** (awrawr-pc, single instance):
   - Appends each new fleet message as `put --text '<json>' -a fleet/<seq>`
   - Runs `sync` to upload to Drive
   - Maintains a persistent local ZIP copy

2. **Reader** (this cell):
   - The `squawk-feed` hook runs `pull` (no‑op when unchanged)
   - Diffs the manifest against its stored cursor to detect new messages
   - Emits new messages to the feed

3. **Consistency Rule**:
   - Never have two writers execute `put`+`sync` without an intervening `pull`
   - Last-writer-wins: re‑putting the same alias replaces the blob and drops the old one

## Operating Rules

1. **Sync unit** – The ZIP is the atomic unit of sync; always `pull` before `put` if another writer may have synced since your last pull.
2. **Blob naming** – Blob names are random per `put`; re‑putting the same alias replaces the blob and drops the old one (manifest updates, old blob becomes orphaned).
3. **State isolation** – The `store/` directory holds the local ZIP + `drive.json` (folder/file ID cache). This is machine‑local state and is never committed to repositories.

## Security Model

**Obfuscation + authenticated access, NOT encryption.**
- Anyone who can read the Drive folder (or obtain the local ZIP) can unzip it and read the contents
- The security boundary is **Google authentication**—nothing in this system is ever served from a public URL
- ⚠️ **Do not use for secrets that must survive Drive compromise**—for those, use the `encrypted-github-fs` vault route instead

## Quick Start

```bash
# Set up the vault (run once)
./runner.sh init

# Add a chat message
./runner.sh put --text '{"user":"alice","msg":"hello"}' -a fleet/000001

# Sync to Drive
./runner.sh sync

# Later, on another machine: pull and list
./runner.sh pull
./runner.sh list
```

## Verification

After running `init`, you should see output confirming:
- Local ZIP creation at `store/vault.zip`
- Drive folder/file IDs
- Successful synchronization

To verify content:
```bash
./runner.sh get fleet/000001  # Should output the JSON text
./runner.sh list --json       # Should show the alias mapping
```

## Dependencies

- **Bash** – for the runner script
- **Standard Unix tools** – `zip`, `unzip`, `jq` (for JSON handling in some operations)
- **Google Drive access** – via either `gws` (hatch) or `rclone` (awrawr-pc)
- **JSON handling** – the manifest and entry payloads are JSON

## Best Practices

- Always `pull` before initiating a write sequence if another writer might have updated the vault
- Use meaningful aliases (e.g. `fleet/<sequence>` or `config/<name>`) for easier debugging
- Monitor the `store/` directory size—the ZIP grows as blobs are added (old blobs are orphaned until cleaned)
- Consider periodic cleanup procedures to remove orphaned blobs if storage becomes a concern
