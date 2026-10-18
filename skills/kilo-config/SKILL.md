---
name: kilo-config
description: >
  Configure kilo/kappa config files: kilo.json, kilo.jsonc, kappa.jsonc.
  Triggers on: "kilo config", "kappa config", "config kilo", "config kappa".
---

# kilo-config Skill

## Purpose

Manage kilo/kappa configuration files (`kilo.json`, `kilo.jsonc`, `kappa.jsonc`) —
small_model selection, model routing, compaction settings, and estate integration.

## When to Use

- Setting `small_model` distinct from `model` to fix compaction breakage
- Configuring provider routing and model preferences
- Editing estate kilo config at `~/.config/kilo/kilo.jsonc`
- Verifying config files after rename (kilo → kappa)

## How to Use

```bash
# View current kilo config
cat ~/.config/kilo/kilo.jsonc

# Edit small_model to fix compaction (T1–T3 from corral spec)
# small_model must be DISTINCT from model

# Validate config parses
bun run script/validate-config.ts
```

## Config Files

| Path | Purpose |
|---|---|
| `~/.config/kilo/kilo.jsonc` | Winning config (takes precedence per names order) |
| `~/.config/kilo/kilo.json` | Fallback config |
| `~/ranch/kappa/kappa-code/mise.toml` | Build task config with forge cache |

## Rules

- `small_model` must be DISTINCT from `model` — identical values cause compaction re-invocation loop
- Never commit secrets; use `{env:...}` for provider keys
- Config change must survive restart and be committed to the owning repo
- Additive only — never disable peers/daemons
