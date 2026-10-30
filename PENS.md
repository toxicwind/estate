# Pens — how the estate organizes code

The estate is the **deploy plane**: it runs the 90+ daemons and ships everything.
But where code is _organized_ is a separate layer — the **pens**.

## The layering (AS DEPLOYED)

```
/home/toxic/
  pens/      where the code pens physically live
     ranch/     the 222-component workspace pen → [toxicwind/ranch](https://github.com/toxicwind/ranch) (GitHub, own git repo)
     olympus/   the Greek-coded pantheon pen → [toxicwind/olympus](https://github.com/toxicwind/olympus) (GitHub, own git repo)
     archive/   junk pen: unreferenced recovered artifacts, .b64 parts, tarballs
  estate/    the deploy plane → [toxicwind/estate](https://github.com/toxicwind/estate) (GitHub)
  pens/      pointer superproject → [toxicwind/pens](https://github.com/toxicwind/pens) (GitHub, organizes olympus/ranch/archive with generators in toolkit/)
```

The pens live locally but are now GitHub-hosted: `ranch` is the workshop workspace
pen (own git repo at [`toxicwind/ranch`](https://github.com/toxicwind/ranch)),
`olympus` is the Greek pantheon registry pen (own git repo at
[`toxicwind/olympus`](https://github.com/toxicwind/olympus)), and `pens` is the
pointer superproject that organizes them all (at
[`toxicwind/pens`](https://github.com/toxicwind/pens)). `estate` is the deploy
plane at [`toxicwind/estate`](https://github.com/toxicwind/estate).

`pens/toolkit/` and `ranch/toolkit/` hold the Bun README/manifest generators that
keep pantheon tables and component metadata in sync.

The estate deploys _through_ the paths: `/home/toxic/pens/estate/ranch/…` maps to
`pens/ranch/…` and `/home/toxic/pens/estate/olympus/…` maps to `pens/olympus/…`.
This is the organization — pens under `pens/`, deploy plane under `estate/`,
both staying path-compatible.

## Which pen is which

| Pen                         | Role                                          | GitHub                                                                                         |
| --------------------------- | --------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| **[estate](https://github.com/toxicwind/estate)** (deploy plane)    | runs the daemons, ships it live, health-checked | [`toxicwind/estate`](https://github.com/toxicwind/estate)                                      |
| **[ranch](https://github.com/toxicwind/ranch)** (workspace pen)     | 222-component workspace pen with `.meta.yaml`   | [`toxicwind/ranch`](https://github.com/toxicwind/ranch)                                        |
| **[olympus](https://github.com/toxicwind/olympus)** (Greek pen)     | registry/pantheon of the Greek-coded products   | [`toxicwind/olympus`](https://github.com/toxicwind/olympus)                                    |
| **[pens](https://github.com/toxicwind/pens)** (pointer superproject) | organizes olympus/ranch/archive with generators | [`toxicwind/pens`](https://github.com/toxicwind/pens) (`toolkit/` holds README/manifest generators) |

## The Greek pen (olympus)

olympus is the **registry of the Greek-coded lineage**: τ tau, κ kappa, skopos,
kilo, muse, keryx, rhodochrosite, kairos, kryptos, agele, mimetite, agon, antilogos,
pylae, propylon, opsis, didymos, chronos-forge, arroyo. Each Greek product
physically lives in `ranch/` (its workspace pen) and is mapped by the
`estate/ranch` path next to its codename in olympus. olympus is the index, not
a place to rip active products out of their pens.

GitHub repo: [`toxicwind/olympus`](https://github.com/toxicwind/olympus) — a clean
pointer/pantheon repo tracking `README.md`, `LICENSE`, `package.json`, `mise.toml`,
`bin/`, and `.gitignore`. `pens/toolkit/` and `ranch/toolkit/` hold the Bun
README/manifest generators.

## Convention

- New component repos are pens under `/home/toxic/pens/` (or stay in an existing
  pen like ranch), registered once — Greek-coded codenames register in olympus.
- All pens are now GitHub-hosted: [`toxicwind/estate`](https://github.com/toxicwind/estate),
  [`toxicwind/pens`](https://github.com/toxicwind/pens),
  [`toxicwind/olympus`](https://github.com/toxicwind/olympus),
  [`toxicwind/ranch`](https://github.com/toxicwind/ranch). The deploy plane
  (`estate`) ships from the pens: "Push → forge build → pitchfork roll → live."
- `pens/toolkit/` and `ranch/toolkit/` hold the Bun README/manifest generators.

## Decluttering `/home/toxic` (in progress)

The home dir accumulated ~535 top-level entries (state, scripts, split `.b64`
parts, tarballs, ad-hoc servers). Target end-state:

```
pens/       ranch, olympus, archive, barn, work, lab  (fully local, no submodules)
estate/     deploy plane only (config, pitchfork, manifest, docs) + symlinks -> pens/
archive/    junk pen: .b64 parts, tarballs, unreferenced recovered artifacts
<dot-state> .local .config .cache .ssh  (the real box infra)
<sacred>    bin, config  (small fixed set)
```

No submodules. Components are plain local git checkouts under `pens/`; the estate
deploy plane symlinks to them.
