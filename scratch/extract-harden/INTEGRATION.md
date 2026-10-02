# Base hardening — integration guide for the merge coordinator

Three new files (add-only; no existing files were touched):

- `/home/toxic/.shingle/chat/fleet_identity.py` — HMAC-SHA256 per-agent signing
- `/home/toxic/.shingle/chat/fleet_wait.py` — inotify fast-path wait, poll fallback
- `/home/toxic/.shingle/chat/fleet_watch.py` — `.channels-index` channel discovery

All three are **stdlib-only**, import-safe (no side effects on import), and were
verified against the base's exact byte-level message format (see `verify_on_read`
round-trip tests: signed file in base `cmd_post` layout verifies; body tamper,
`from` forgery, missing hmac, and missing key all fail closed naming the agent).

---

## 1. fleet_identity.py — wire it into post / read / wait

### Key directory (NEVER inside the chat root)

`/home/toxic/.shingle/keys/<agent_id>.key` — 64 lowercase hex chars (32 bytes),
mode `0600`; directory mode `0700`. Override for tests via `FLEET_KEYS_DIR` env.

**Recommended keygen CLI UX** (add a `keygen` subcommand to chat.py, or run the
module directly — both work):

    python3 fleet_identity.py keygen <agent_id>            # refuses to clobber
    python3 fleet_identity.py keygen <agent_id> --force    # rotate
    python3 chat.py keygen <agent_id>                      # if you add the subcommand

Run once per fleet agent as user `toxic`. Agent ids must match
`[A-Za-z0-9][A-Za-z0-9_-]{0,63}` — the same traversal guards as
`_check_safe_name` (keygen rejects `../evil`, leading `.`/`_`, etc.).

### The hmac field in frontmatter

One line, placed **LAST before the closing `---`**:

    ---
    seq: 7
    from: agent-a
    to: all
    channel: ops
    ts: 2026-09-14T05:00:00+00:00
    status: discussion
    title: hello
    hmac: <64 hex chars>
    ---

`parse_frontmatter()` ignores unknown keys, so old readers keep working; only
`verify_on_read()` enforces the signature.

### Exact edits for chat.py

**`cmd_post`** (base lines ~558-600): after the `fm` list is built and the seq
lock is held, sign the canonical bytes and append the field before the closing
`---`. Concretely, change:

```python
        fm += [
            f"channel: {channel}",
            f"ts: {timestamp}",
            f"status: {status}",
            f"title: {title}",
            "---",
            "",
        ]
```

to:

```python
        import fleet_identity  # top of file in real integration
        sig = fleet_identity.sign(
            a.sender,
            fleet_identity.canonical_message(
                seq=seq, sender=sender, to=to, reply_to=reply,
                channel=channel, ts=timestamp, status=status,
                title=title, body=body,
            ),
        )
        fm += [
            f"channel: {channel}",
            f"ts: {timestamp}",
            f"status: {status}",
            f"title: {title}",
            f"hmac: {sig}",
            "---",
            "",
        ]
```

Pass the already-`_frontmatter_value`'d locals (`sender`, `to`, …);
`canonical_message` re-applies the same fold+strip normalization that
`parse_frontmatter` performs on read, so sign/verify agree byte-for-byte.
`sign()` raises `FleetIdentityError` naming the agent when that agent has no
key — let it propagate (fail closed: no key, no post).

Canonical serialization (documented in the module; do NOT change field order
or normalization without bumping `CANONICAL_VERSION`):

    fleet-chat-v1\n
    seq: <int>\nfrom: <sender>\nto: <to>\nreply_to: <or empty>\n
    channel: <channel>\nts: <ts>\nstatus: <status>\ntitle: <title>\n
    body-sha256: <sha256 hex of body with CRLF->LF then rstrip()>\n

The body is covered via its digest (it holds arbitrary markdown/newlines).
`body-sha256` uses exactly what `cmd_post` writes: `body.rstrip()` after the
single blank line following the closing `---`.

**`cmd_read`** (base ~603-640): in the `for seq, p in found:` loop, verify
before printing:

```python
    for seq, p in found:
        meta = parse_frontmatter(p)
        if not a.all and not is_relevant(meta, a.agent):
            continue
        try:
            fleet_identity.verify_on_read(p)   # fail CLOSED
        except fleet_identity.FleetIdentityError as e:
            die(f"identity check failed: {e}")  # names the agent; abort the read
        _print_message(p)
        shown += 1
```

**`cmd_wait`** (base ~641-685): same check in the `for p in found:` loop
before `_print_message(p)`.

`verify_on_read(path) -> dict` returns the parsed frontmatter (minus `hmac`)
on success and raises `FleetIdentityError` — always naming the agent — for:
missing `hmac` field, empty `from`, missing/malformed key file, digest
mismatch. **Migration warning:** pre-existing unsigned archive messages will
be REJECTED. One-time migration (requires every sender's key present):

    python3 fleet_identity.py sign-archive <channel_dir>

which inserts the `hmac:` line into each unsigned message in place.

### Debug helper

    python3 fleet_identity.py verify-file <message.md>   # prints OK or the error

---

## 2. fleet_wait.py — replace the sleep-poll loop

**`cmd_wait`** (base ~641-685): replace the whole `while True:` /
`time.sleep(a.interval)` loop with:

```python
def cmd_wait(root: Path, a):
    import fleet_wait, fleet_identity
    d = require_channel(root, a.channel)
    cur = read_cursor(d, a.agent)
    deadline = time.time() + a.timeout
    while True:
        remaining = deadline - time.time()
        found = fleet_wait.wait_for_new_messages(d, cur, max(0.0, remaining))
        if found:
            for p in found:
                meta = parse_frontmatter(p)
                if not is_relevant(meta, a.agent):
                    continue
                try:
                    fleet_identity.verify_on_read(p)
                except fleet_identity.FleetIdentityError as e:
                    die(f"identity check failed: {e}")
                _print_message(p)
            write_cursor(d, a.agent, max_seq(d))
            return
        # found == [] means the timeout expired (no new relevant messages)
        print(f"(timeout after {a.timeout}s: no new messages for {a.agent} "
              f"in '{a.channel}')", file=sys.stderr)
        raise SystemExit(2)
```

Notes for the integrator:

- `wait_for_new_messages(channel_dir, since_seq, timeout) -> list[Path]`
  returns message files with `seq > since_seq` sorted by seq, `[]` on timeout.
  Relevance filtering (`is_relevant`) and cursor advance stay in chat.py, as
  above — the helper is deliberately relevance-agnostic so it can also serve
  other watchers.
- Inotify (ctypes → libc, no third-party) is used on Linux; the watch is
  armed **before** the initial scan, so no message can slip between check and
  wait. `IN_Q_OVERFLOW` triggers a rescan rather than trusting the stream.
- Non-Linux, or any inotify failure at runtime, degrades to an
  `os.scandir` poll (0.5 s ticks). The `--interval` flag can be kept as the
  poll quantum for the fallback path, or dropped.
- Zero-token property kept: blocks in-process, no subprocess, no network.
- Seq parsing mirrors base `_seq_from_name` exactly, including the
  `isdecimal()` (not `isdigit()`) guard against unicode superscripts.

---

## 3. fleet_watch.py — channel discovery for the WhatsApp side

**`cmd_init`** (base ~417-440): after `_meta.json` is written successfully
(so a crashed init never indexes a half-made channel), add:

```python
    import fleet_watch
    fleet_watch.note_channel(root, a.channel)
```

This appends one line to `CHAT_ROOT/.channels-index` (O_APPEND, atomic for
short lines):

    2026-09-14T05:03:12+00:00<TAB>ops

Name validation mirrors base `_check_safe_name` plus tab/CR/LF rejection
(line-format integrity). The index file is created on first use; readers must
handle it not existing yet (fresh root).

**WhatsApp-side tail loop** (reader contract):

```python
import fleet_watch
off = load_stored_offset()          # 0 on first run
seen = set()
while True:
    for off, name in fleet_watch.watch_channels(root, off):
        if name not in seen:
            seen.add(name)
            on_new_channel(name)    # join / roster / whatever
    store_offset(off)
    time.sleep(30)                  # or inotify-watch the single index file
```

`watch_channels(root, since_offset)` yields `(offset_after_line, name)` for
well-formed lines past the offset; malformed lines are skipped but their
bytes are jumped over by the next well-formed line's offset. Dedupe by name
on the reader side (`init` already refuses duplicates; the reader dedupe is
belt-and-braces).

**Backfill:** existing channels created before this lands need one line each:

    python3 -c "
    import fleet_watch, sys
    from pathlib import Path
    root = Path(sys.argv[1])
    for d in sorted(root.iterdir()):
        if d.is_dir() and (d / '_meta.json').exists():
            fleet_watch.note_channel(root, d.name)
    " "$CHAT_ROOT"

---

## Test report (2026-09-14, sandbox + awrawr-pc)

- 30/30 local checks pass: keygen (incl. clobber/traversal/prefix refusal),
  sign/verify round-trip, tamper (body) detection, forged-`from` rejection,
  unsigned rejection, unknown-agent fail-closed both directions, wrong-agent
  key mismatch, `sign-archive` migration + idempotency, CLI `verify-file`,
  inotify wait returning a message posted 0.4 s later in <3 s, timeout → `[]`,
  `timeout=0` single scan, poll-fallback timeout, seq-parsing parity with base
  (`²` rejected, `0007-…` → 7), watch index (missing file, offsets, resume,
  tab-separated lines, bad-name rejection).
- On awrawr-pc: all three modules `py_compile` clean under Python 3.14.6 and
  the inotify smoke test (post-then-wait) passes on the live box.

## Could NOT verify / open decisions for you

1. **Key distribution is out of band.** `keygen` must be run once per fleet
   agent as user `toxic` on awrawr-pc. There is no enrollment protocol here —
   whoever holds the box can mint a key for any id, which is correct for a
   single-box fleet but means keygen itself needs the box's existing access
   controls (it does: files are 0600 under `~/.shingle/keys`, dir 0700).
2. **Archive migration is your call.** `verify_on_read` fails closed, so
   flipping it on rejects every pre-existing unsigned message until
   `sign-archive` runs. Decide: migrate-then-enforce, or enforce-only-new.
3. **`--interval` fate** in `cmd_wait`: keep it as the poll-fallback quantum
   or drop the flag. I recommend keeping it (harmless, useful off-Linux).
4. **Event messages** (`event post`, base ~856-895) write a different
   frontmatter shape — I did not wire signing for them. Either route event
   posts through the same `hmac:` field (canonical fields differ; needs a
   `canonical_event()` variant) or leave events unsigned and document it.
5. **No replay protection.** HMAC binds content+sender but a captured signed
   file could be re-posted under a new seq by anyone with the file. The seq
   lock + filename make casual replay visible, but true replay resistance
   (nonce / monotonic per-sender counter) is future work.
