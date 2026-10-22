# Pens — how the estate organizes code

The estate is the **deploy plane**: it runs the 90+ daemons and ships everything.
But where code is _organized_ is a separate layer — the **pens**.

## The layering (AS DEPLOYED)

```
/home/toxic/
  pens/      where the code pens physically live (non-GitHub workspace/home) — ORGANIZATION
     ranch/     the 169-component workspace pen (one dir per component)
     olympus/   the Greek-coded pantheon pen (the `toxicwind/olympus` repo)
  estate/    the deploy plane  (GitHub: toxicwind/estate)
     ranch   ->  /home/toxic/pens/ranch    (symlink: deploy plane resolves to the pen)
     olympus ->  /home/toxic/pens/olympus  (symlink)
GitHub       remote home for each component (toxicwind/<name>)
```

The estate deploys _through_ the symlinks: `/home/toxic/estate/ranch/…` keeps
working and is just `pens/ranch/…`. This is the organization — code pens under
`pens/`, the deploy plane under `estate/`, both staying path-compatible.

## Which pen is which

| Pen                       | Role                                            | GitHub                      |
| ------------------------- | ----------------------------------------------- | --------------------------- |
| **estate** (deploy plane) | runs the daemons, ships it live, health-checked | `toxicwind/estate`          |
| **ranch** (workspace pen) | one directory per component; the source mesh    | each component its own repo |
| **olympus** (Greek pen)   | registry/pantheon of the Greek-coded products   | `toxicwind/olympus`         |

## The Greek pen (olympus)

olympus is the **registry of the Greek-coded lineage**: τ tau, κ kappa, skopos,
kilo, muse, keryx, hodos, kairos, kryptos. Each Greek product physically lives
in `ranch/` (its workspace pen) and is mapped by the `estate/ranch` path next to
its codename in olympus. olympus is the index, not a place to rip active
products out of their pens.

## Convention

- New component repos are pens under `/home/toxic/pens/` (or stay in an existing
  pen like ranch), registered once — Greek-coded codenames register in olympus.
- The deploy plane (`estate`) stays GitHub-hosted; the pens are the organization
  layer. "Push → forge build → pitchfork roll → live" ships from the pens
  through estate.
