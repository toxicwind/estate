---
name: herd-to-agele-roundup
description: >
  Rename-roundup procedure for rebranding herd (local llama-swap inference router
  on :25100) to its Greek pantheon codename agele (ἀγέλη, "herd") and relocating
  it into pens/olympus/products/agele with additive ranch symlinks.
---

# Herd → Agele (ἀγέλη) Greek Rename Roundup & Olympus Relocation

## Why `agele` (ἀγέλη)
In Ancient Greek, **ἀγέλη (`agele`)** literally means **"herd"** (specifically a herd of cattle/oxen or horses, from ἄγω "to lead/drive"). It joins the Olympus Greek pantheon (`tau`, `kappa`, `hodos`, `keryx`, `skopos`, `kairos`, `kryptos`, `pinax`, `agon`, `antilogos`, `pylae`, `propylon`, `opsis`, `didymos`) while keeping the exact semantic meaning of `herd` 🐂.

- Availability verified via `name-check.ts agele`: **0 external conflicts** across pitchfork, ranch, ports.env, mise, config, and binaries.
- Separation from **Hodos (ὁδός)**:
  - **Agele (`:25100`)** is the local on-box GGUF / `llama-swap` front door (`http://127.0.0.1:25100/v1`).
  - **Hodos (`:25193`)** is the cloud provider router (`http://127.0.0.1:25193/v1`).
  - In `~/.config/kappa/kappa.jsonc`, `agele` and `hodos` are distinct providers so Hodos never mislabels local `agele`/`herd` models.

## Procedure

### 1. Check Name Availability
```bash
bun run /home/toxic/estate/grasp-hub/skills/00_inbox/rename-roundup/name-check.ts agele
```

### 2. Run Rename Roundup (`name-fix.ts`)
```bash
bun run /home/toxic/estate/grasp-hub/skills/00_inbox/rename-roundup/name-fix.ts \
  herd agele --repo /home/toxic/pens/olympus/products/agele --execute --force
```
Note: The Go module path `github.com/mostlygeek/llama-swap` is intentionally preserved so Go package imports remain zero-friction across upstream syncs.

### 3. Physical Location in Olympus + Additive Symlinks
- **Canonical path**: `/home/toxic/pens/olympus/products/agele`
- **Olympus top-level link**: `/home/toxic/pens/olympus/agele -> products/agele`
- **Ranch links (additive compatibility)**:
  - `/home/toxic/pens/ranch/agele -> /home/toxic/pens/olympus/products/agele`
  - `/home/toxic/pens/ranch/herd -> /home/toxic/pens/olympus/products/agele`
  - `/home/toxic/pens/olympus/products/agele/config/herd.yaml -> agele.yaml`

### 4. Regenerate Pantheon Registry
```bash
/home/toxic/pens/pensctl generate-all
```
