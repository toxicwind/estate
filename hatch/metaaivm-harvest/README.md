# metaaivm-harvest

GitHub-wide harvest for `metaaivm`-related keywords, collected 2026-09-30.

## What `metaaivm` is

Meta AI's VM transport family: hosts like `hatch.metaaivm.com` and
`wss://<vm-id>.metaaivm.com/` serve the Muse AI agent backend over a
Noise_XX-secured WebSocket gateway. The estate already speaks this protocol:
`toxicwind/metaclaw-runtime` ships a `MetaAiVmClient` (Noise_XX handshake,
RPC framing, `src/vm/client.js`).

## Contents

- `manifest.json` - query record, counts, method, fork decision
- `code_raw.json.gz` - all 300 code-search items (gzip)
- `repos.json` - 99 unique repos deduped by full_name, with matched paths
- `issues.json` / `prs.json` - full search metadata (3 issues, 4 PRs)
- `candidates/` - key excerpts from fork candidates

## Key findings

- Zero standalone metaaivm project repos on GitHub.
- 3 issues, 4 PRs; the live ones are `nikships/muse-cli#1` (gateway WebSocket
  TLS verification) and `kleprevost/muse-mcp#1` (same fix, PR form).
- Fork target: `nikships/muse-cli` -> `toxicwind/muse-cli`.
