# matter-server canonical dependency mirror

The live app runs from `/home/toxic/.matter-server/app` (outside this repo).
These two files are the canonical, committed mirror of that directory's
dependency manifests:

- `package.json` — single dependency: `matter-server@^1.4.0`
- `package-lock.json` — the pinned, integrity-hashed closure

Rebuild after a wipe:

```bash
mkdir -p /home/toxic/.matter-server/app
cp tools/matter-server/package.json tools/matter-server/package-lock.json \
   /home/toxic/.matter-server/app/
cd /home/toxic/.matter-server/app && npm ci --no-audit --no-fund
```

`bin/daemon-deps-verify` verifies the LIVE app dir directly (lockfile
presence + node_modules completeness). If the live manifests ever change,
copy them back here so the mirror stays canonical.
