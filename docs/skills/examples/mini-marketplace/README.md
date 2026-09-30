<div align="right">

[![License: MIT](https://img.shields.io/badge/license-MIT%20%2B%20upstream-blue?style=for-the-badge)](https://github.com/toxicwind/sovereign-projects#license)
[![sovereign-projects](https://img.shields.io/badge/part_of-sovereign--projects-blue?style=for-the-badge)](https://github.com/toxicwind/sovereign-projects)

</div>

# mini-marketplace

> **The smallest possible `omp` marketplace — one catalog, one plugin, zero magic.**

A minimal `omp` marketplace catalog that demonstrates the `marketplace.json` format. It lists one plugin (`my-plugin`) using a relative path source.

```mermaid
flowchart LR
    cat[marketplace.json<br/>catalog] --> rel[relative-path plugin source<br/>./my-plugin]
    rel --> add[/marketplace add ./mini-marketplace]
    add --> inst[/marketplace install my-plugin@example-marketplace]
    inst --> run[plugin live in omp]
```

## Install command

```
/marketplace add ./docs/skills/examples/mini-marketplace
/marketplace install my-plugin@example-marketplace
```

Or from the CLI:

```
omp plugin marketplace add ./docs/skills/examples/mini-marketplace
omp plugin install my-plugin@example-marketplace
```

## What it demonstrates

- Minimum required `marketplace.json` fields: `name`, `owner.name`, `plugins`
- Relative path plugin source using `./` prefix (`"source": "./my-plugin"`)
- Plugin bundled inside the same directory tree as the marketplace catalog
- Extra catalog metadata: the example includes a top-level `description`; current marketplace parsing preserves extra top-level fields, while runtime behavior uses required fields and plugin entries.

## Structure

```
mini-marketplace/
  .claude-plugin/
    marketplace.json      ← catalog
  README.md
  my-plugin/
    package.json          ← omp.extensions manifest
    index.ts              ← extension entry point
```

Published and local marketplaces use the same catalog location. omp loads `.omp-plugin/marketplace.json` first and falls back to `.claude-plugin/marketplace.json` (the Claude Code-compatible path this example ships) inside the marketplace root. Point `/marketplace add` at this folder to load the example.

## License & Security

MIT where marked — [license](https://github.com/toxicwind/sovereign-projects#license). These are minimal example extensions: safe to copy and adapt. Never drop a real secret into an example config; treat any key-shaped string in docs as untrusted until verified.
