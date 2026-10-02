# INTEGRATION.md -- fleet_gossip.py -> chat.py `gossip` command

Paper steal #1 (Demers et al. 1987 anti-entropy). Module is complete and
self-tested at `/home/toxic/.shingle/chat/fleet_gossip.py` (stdlib only,
no chat.py imports; mirrors `_check_safe_name`/`slugify`/`_seq_from_name`
by hand like fleet_log.py does). This file proposes the chat.py wiring.
The coordinator owns all edits below -- this worker adds files only.

## Proposed CLI

```
python3 chat.py gossip --agent <id> [--channel <ch>] [--repair|--no-repair] [--json]
```

- `--agent` (required): whose digest is written to `.digests/<agent>.json`
  and who the report is "for".
- `--channel` (optional): scope the pass to one channel; default is all
  channels (the `cmd_channels` filter: visible dirs with `_meta.json`).
- `--repair` (default): run backfill for gaps recoverable from log.jsonl.
  `--no-repair`: scan + digests only, report only.
- `--json`: print the raw `anti_entropy()` report dict as JSON; otherwise
  print a short human summary (channels scanned, gaps, recovered,
  unrecoverable, divergent) and exit nonzero if `unrecoverable` or
  `errors` is non-empty.

## Suggested chat.py wiring (coordinator to write)

```python
from fleet_gossip import (
    anti_entropy as gossip_anti_entropy,
    scan_gaps as gossip_scan_gaps,
    write_digest as gossip_write_digest,
    compare_digests as gossip_compare_digests,
)

def cmd_gossip(root, a):
    # a.agent, a.channel (optional), a.repair (bool), a.json (bool)
    if a.channel:
        from fleet_gossip import scan_gaps, backfill
        gaps = scan_gaps(root, a.channel)
        bf = backfill(root, a.channel) if a.repair else None
        ...print / json...
    else:
        report = gossip_anti_entropy(root, a.agent) if a.repair \
            else gossip_scan_only(root, a.agent)
        ...
```

argparse:

```python
s = sub.add_parser("gossip", help="anti-entropy repair pass (scan gaps, backfill from log, compare digests)")
s.add_argument("--agent", required=True)
s.add_argument("--channel", default=None)
s.add_argument("--repair", dest="repair", action="store_true", default=True)
s.add_argument("--no-repair", dest="repair", action="store_false")
s.add_argument("--json", action="store_true")
```

For `--no-repair` the module currently has no single "scan-only" entry;
either call `anti_entropy` and ignore its backfill (it already ran --
not acceptable for a no-repair flag) or add a tiny wrapper in chat.py:

```python
def gossip_scan_only(root, agent):
    from fleet_gossip import _channels, scan_gaps, write_digest, compare_digests
    ...
```

Prefer adding a `scan_only(root, agent)` function to fleet_gossip.py in a
follow-up (worker can do it) rather than reaching into privates.

## Semantics the coordinator should preserve

1. **gossip never allocates seqs** -- it only fills specific missing ones
   from the log, so it needs no channel seq lock. Safe to run
   concurrently; racing backfills write byte-identical content.
2. **recovered files are marked**: `status: recovered`,
   `title: <type>-recovered`, `recovered_from: log.jsonl` in frontmatter.
   They parse with the existing `parse_frontmatter`.
3. **digest stability**: digests hash filenames+mtimes; message files are
   write-once, backfill never overwrites, so digests only change when the
   channel really changed.
4. **`.digests/` is hidden** (leading dot), same as `.archive/` and
   `.cursors/`, so `cmd_channels` ignores it.
5. **digest format**: `write_digest` writes `.digests/<agent>.json` as a
   wrapped object (`format`/`agent`/`written_at`/`channels`).
   `read_digest`/`compare_digests` also accept the bare
   `{channel: hex}` mapping form, so if the coordinator prefers the
   simpler bare mapping from the original spec, readers keep working
   either way. Coordinator's call; no module change needed.

## Backfill fidelity gap (composition point with fleet_log.py)

log.jsonl records carry only `seq/ts/agent/type/body`. Backfill therefore
cannot restore `to`, `reply_to`, `title`, or the original `status`; it
defaults `to: all` and marks `status: recovered`. If the log schema ever
gains optional `to`/`title`/`reply_to` fields (append-only, backward
compatible), the `# backfill-fidelity` marker in fleet_gossip.py shows
exactly where to prefer them. This is a coordinator/schema decision, not
a worker change.

## Suggested cadence

No daemon in the module by design. Natural homes: a cron every 15 min
(`chat.py gossip --agent <id> --json` piped to the fleet snapshot), or a
`post`/`read` hook. The 15-minute fleet snapshot digest already exists --
gossip output drops straight into it.
