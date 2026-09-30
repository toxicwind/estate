# matter-server canonical dependency mirror

<div align="right">

[![License: MIT](https://img.shields.io/badge/license-MIT%20%2B%20upstream-blue?style=for-the-badge)](https://github.com/toxicwind/sovereign-projects#license)
[![sovereign-projects](https://img.shields.io/badge/sovereign--projects-monorepo-blue?style=for-the-badge)](https://github.com/toxicwind/sovereign-projects)

</div>

The live Matter app runs from `/home/toxic/.matter-server/app` — outside
this repo, wipable at any time. These two files are the **canonical,
committed mirror** of that directory's dependency manifests, so a wiped box
rebuilds bit-identically:

- `package.json` — single dependency: `matter-server@^1.4.0`
- `package-lock.json` — the pinned, integrity-hashed closure

```mermaid
flowchart LR
    live[/home/toxic/.matter-server/app/ · live] -->|copy back on change| mirror[this dir · canonical]
    mirror -->|npm ci| rebuild[bit-identical rebuild after wipe]
    verify[bin/daemon-deps-verify] -.->|lockfile + node_modules check| live
```

## Quick start

Rebuild after a wipe:

```bash
mkdir -p /home/toxic/.matter-server/app
cp tools/matter-server/package.json tools/matter-server/package-lock.json \
   /home/toxic/.matter-server/app/
cd /home/toxic/.matter-server/app && npm ci --no-audit --no-fund
```

## Architecture

This directory holds manifests only — no source, no app code. The live app
dir is the runtime; this repo is the record. If the live manifests ever
change, copy them back here so the mirror stays canonical.

## Config

None. The pin is the config: `matter-server@^1.4.0` with the locked
closure in `package-lock.json`.

## Dev / contributing

[`../../bin/daemon-deps-verify`](../../bin/daemon-deps-verify) verifies the LIVE app dir directly (lockfile
presence + `node_modules` completeness). After any dependency change,
mirror the live manifests here and commit.

## License & security

MIT — see [LICENSE](https://github.com/toxicwind/sovereign-projects#license).

Manifests only — no secrets, no code. `npm ci` (not `npm install`) keeps
the install reproducible from the lockfile.
