# fleet_delta.py -- INTEGRATION.md

Delta-state sync for the emergent agent-chat fork (paper steal #10:
Almeida, Shoker, Baquero 2017). Slow-path agent (WhatsApp side) asks for a
compact "what's new" without scanning every channel. New file:
`/home/toxic/.shingle/chat/fleet_delta.py` (stdlib only).

## API (already built and self-tested)

* `load_vector(root, agent) -> dict[channel, last_seen_seq]`
  Reads `<root>/.vectors/<slug(agent)>.json`. `{}` when missing. Corrupt
  file raises `chat.AgentChatError` (fail loud, never silently resend all).
* `save_vector(root, agent, vector)` -- atomic tmp + os.replace.
* `migrate_from_cursors(root, agent) -> dict` -- folds the base's
  per-channel `.cursors/<slug>.txt` into the vector via `chat.read_cursor`.
  **Leaves the .cursors files in place** so `chat.py read` is unaffected.
* `delta(root, agent) -> {channel: [Paths with seq > vector[channel]]}` --
  ALL channels in one call, `(channel, seq)` sorted. Auto-migrates on first
  use (no vector file -> `migrate_from_cursors`).
* `advance(root, agent, new_vector)` -- persist after a successful read.
* `delta_digest(root, agent, relevant_only=True) -> list[str]` -- one line
  per unread message: `<channel> #<seq> <from>-><to> <lamport> <body..80>`.
  Example: `ops #0002 yote->main 2 main-only note about the router`

Reused from the base (imported, never re-implemented): `read_cursor`,
`slugify`, `_seq_from_name`, `channel_dir`, `parse_frontmatter`,
`is_relevant`, `AgentChatError`. Channel enumeration mirrors the base's
`channels` command (non-hidden dirs with `_meta.json`); the body snippet
extractor is new (base has none).

## Design decisions worth knowing

1. **Vector lives at root level, not per-channel.** One JSON read covers all
   channels -- exactly what the slow path wants. Per-channel files would
   reintroduce the scan we're avoiding.
2. **Lamport = seq.** Base frontmatter has no lamport field. Each channel's
   seq counter is monotonic under the atomic-mkdir lock, i.e. it IS that
   channel's Lamport clock, so the digest's lamport column is the seq. If a
   true cross-channel lamport field is ever added to post frontmatter, swap
   the one line in `delta_digest`.
3. **Digest filters by relevance by default** (`chat.is_relevant`, which
   delegates to fleet_addr): `to` is a wake hint, broadcast is visible.
   `relevant_only=False` gives the full firehose.
4. **priv-* channels:** message bodies on disk are ciphertext (fleet_e2ee).
   The digest shows an opaque ciphertext snippet -- no plaintext leak. A key
   holder can decrypt via `fleet_e2ee.decrypt_message(channel, blob)`; the
   slow-path consumer can do that on the lines it cares about. Keep
   decryption out of the delta path (stdlib-only promise).
5. **No writes to .cursors.** Migration is read-only; vector and .cursors can
   drift if an agent uses both `read` and `digest`. Old .cursors files may
   be pruned by the coordinator once `digest` is the only reader for an
   agent -- not done here, deliberately reversible.

## Proposed `chat.py digest` command (coordinator: wire into build_parser)

```python
p = sub.add_parser("digest", help="slow-path what's-new digest across all channels")
p.add_argument("--agent", required=True)
p.add_argument("--peek", action="store_true",
               help="print digest but do not advance the vector")
p.add_argument("--all", action="store_true",
               help="include messages not addressed to --agent")
p.set_defaults(func=cmd_digest)

def cmd_digest(root, a):
    import fleet_delta as fd
    vec = fd._ensure_vector(root, a.agent)          # or fd.load_vector + migrate
    deltas = fd.delta(root, a.agent)
    for line in fd.delta_digest(root, a.agent, relevant_only=not a.all):
        print(line)
    if not a.peek and deltas:
        adv = dict(vec)
        for ch, paths in deltas.items():
            adv[ch] = max(adv.get(ch, 0),
                          max(fd.chat._seq_from_name(p.name) for p in paths))
        fd.advance(root, a.agent, adv)
        print(f"(vector advanced for {a.agent})", file=sys.stderr)
```

Notes for the wiring: `delta_digest` already calls `delta` internally, so the
sketch above scans twice -- acceptable for a slow-path command, or hoist the
vector update into the digest path later. `--peek` mirrors the base `read
--peek` semantics (look without advancing). Consider `digest --watch` later
by pairing with `fleet_watch.py`'s `.channels-index` for new-channel
discovery plus vector sync for new-message discovery.

## Verification

`cd /home/toxic/.shingle/chat && python3 fleet_delta.py selftest`
exercises migrate -> delta -> digest -> advance -> quiet on a throwaway root.
