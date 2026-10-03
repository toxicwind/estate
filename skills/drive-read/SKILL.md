---
name: "drive-read"
description: "Autonomous Google Drive file reader — metadata-routed download/export that never surfaces the binary-download 403."
---

# drive-read

`~/workspace/bin/drive-read` — the autonomous Drive read shim. Use it instead
of raw `hatch_gws_cli drive files download` whenever you need a Drive file's
*contents*.

## Why it exists

`drive files download` 403s on Google-native files with the artificial error
"Only files with binary content can be downloaded. Use Export with Docs
Editors files." The vendored google-drive skill then instructs agents to stop
and ask for the Docs/Sheets/Slides skill — a flail loop for what is a
mechanical routing decision. This shim makes the routing decision itself, so
the error class disappears.

## Usage

```sh
drive-read <file-id> [--mime <export-mime>] [--out <path>] [--meta]
```

- No flags: print the file's text content to stdout.
- `--meta`: print JSON metadata only — `{id, name, mimeType, route, exportMime}`.
- `--out <path>`: write content to `<path>` instead of stdout (for binary).
- `--mime`: override the export MIME type.

## Routing

The shim fetches metadata first, then:

| mimeType | route |
|---|---|
| `application/vnd.google-apps.document` | `drive files export` as `text/plain` |
| `application/vnd.google-apps.spreadsheet` | `drive files export` as `text/csv` |
| `application/vnd.google-apps.presentation` | `drive files export` as `text/plain` |
| other `vnd.google-apps.*` | `drive files export` as `text/plain` |
| everything else | `drive files download` (binary-safe: text cats, binary reports path) |

Exports/downloads go through a temp file (`-o`) because the CLI refuses to
emit file bytes to stdout in this environment ("needs an explicit --output
path") — the shim absorbs that second artificial error too.

## Notes

- Exit 0 on success; clean `{"ok":false,"error":...}` JSON on stderr on failure.
- Corrupted source content (e.g. binary pasted into a Doc) comes back as-is —
  the shim fixes routing, not the file.
- yote has no `hatch_gws_cli` and no Google credentials: this shim is
  cell-only. Do not attempt to add it as a yote MCP tool.
