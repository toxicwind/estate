# Zero-* Primitives Register (2026-10-22, /home/toxic full scan)

Regex-inventoried: files/dirs matching `zero-*`, `*zero-transport*`, `zero_transport*`,
plus the `true-zero-copy-*` family. 32 items total. This doc is the durable catalog so
the zero-* primitives are findable/known, not scattered.

## The core primitive: `zero-transport`
A small C transport library (raw packet write/read with proto framing). Files:
- `pens/ranch/zero-transport/zero_transport.{c,h}` + built `libzero_transport.so` (15.9KB) —
  TRACKED in `toxicwind/ranch` (recognized 2026-10-15). Canonical.
- `~/src/zero_transport.{c,h}` — mirror (2026-10-15).
- `install_zero_transport.sh` — installer.
Carried by the <ranch>-<name> worktrees (the "word-in-front" matches):
- `~/kite/worktrees/ranch-{pry,sable,finch,forge,osprey,forge-archguard}/zero-transport`

## Related-but-distinct (do NOT conflate)
- `true-zero-copy-pcie-streaming` — azurite skill (PCIe zero-copy), different thing.
- `src/local/codeprobe/docs/zero-code-access` — code access docs.
- `utf8-zero` — a Rust crate in cargo registry cache (unrelated).
- nuclei-templates `agent-zero-detect` / `zerof-webserver-detect` / `zeroshell-*` — security templates (unrelated scanners).
- `sigma/tests/*zero-config-routing*` + `issue793-zero-usage-abort.test.ts` — tests.

## Docs
- `tmp/docs/zero-transport-audit-2026-10-14.md`
- `pens/olympus/products/tau/zero-transport.md`
- `sovereign/skills/true-zero-copy-pcie-streaming` + azurite/flat symlinks

## Notes
- The zero-* search is best done with `find ... -iname 'zero-*' -o -iname '*zero-transport*'` (word-in-front via the worktree pattern ranch-*).
- Catalog regenerated on demand; see `/home/toxic/pens/estate/bin/delend-route` for routing a "zero-transport" intent to the right primitive.
