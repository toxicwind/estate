# host-proof

Universal read-only host proof bundle. Identifies whatever box it runs on --
no hardcoded hostnames. Two implementations, one contract:

- `proof-bundle.bun.js` -- maximal proof artifact (preferred when `bun` exists).
  Every command's stdout is hashed (sha256 + bun hash) and recorded as JSON.
  Records append to `manifest.jsonl` incrementally (crash-resilient). The final
  `manifest.json` is checksummed into `manifest.sig` for post-run integrity
  verification. Includes assertions (M) and a signed manifest (N).
- `host-audit.sh` -- zero-dependency bash fallback. Labeled sections A-I with
  `CHECK-UNAVAILABLE` branches instead of assumptions. Stdout only.
- `run.sh` -- picks bun when present, else bash. Sets a unique `OUT` dir.

## Run

```bash
./run.sh
# or, with an explicit output dir for the bun bundle:
OUT=~/host-proof-runs/mychat bun proof-bundle.bun.js
# bash fallback takes an optional entity-hunt target (defaults to hostname):
./host-audit.sh
TARGET=mybox ./host-audit.sh
```

## Verify (bun bundle)

```bash
sha256sum <OUT>/manifest.json
cat <OUT>/manifest.sig
```

The two hashes must match. If they do not, the manifest was modified after
the run completed.

## Secret hygiene

Environment values are never printed -- only presence, sha256, and length.
Config files (e.g. MCP configs) are hashed, never dumped.

## History

Supersedes the `awrawr-proof` v3-bun draft. Fixes a parse-time SyntaxError in
that draft (a `${n##*/}` inside a JS template literal -- JS interpolation,
not shell). Schema is now `host-proof-bundle/v1`.
