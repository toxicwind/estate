# Common tasks

Recipes for using the `hashline` tool from a Pi coding agent.

## Replace a single line

Given a `read` result:

```
12:  return input;
```

replace it with a call to `next(input)`:

```
[src/foo.ts#A1B2]
SWAP 12.=12:
+  return next(input);
```

## Delete a range without a replacement body

Empty `SWAP` bodies are rejected. Use `DEL` instead:

```
[src/foo.ts#A1B2]
DEL 12.=15
```

## Insert a banner after an import block

```
[src/foo.ts#A1B2]
INS.POST 7:
+// added banner
+
```

## Rename a file while editing it

Line edits above `MV` apply to the source; the final content is written
at `DEST`:

```
[src/old.ts#A1B2]
SWAP 3.=3:
+export const NEW_NAME = 1;
MV src/new.ts
```

## Multi-file atomic edit

All sections are parsed and preflighted before any commit. A stale tag,
missing anchor, or empty body on **any** section aborts the whole patch
before disk is touched:

```
[src/a.ts#A1B2]
SWAP 1.=1:
+A

[src/b.ts#C3D4]
DEL 5.=6
```

## Recover from a stale-tag rejection

The extension responds with a re-`read` instruction and the fresh tag
for the affected paths. Re-`read` those paths, then re-author the patch
against the new snapshot. Do not paper over the rejection by editing
the tag by hand — it exists to catch exactly this drift.

## Verify a change locally

```sh
bun run check   # biome + tsc --noEmit + bun test
```

`bun run check` is what CI runs on every push and pull request
(`.github/workflows/check.yml`). This repository is distributed from
GitHub only — there is no npm-publish step. See the "Distribution
model" section of `CONTRIBUTING.md` for the rationale.
