# INTEGRATION.md — wiring `fleet_log.py` into chat.py

`fleet_log.py` (`/home/toxic/.shingle/chat/fleet_log.py`) is a **new file only**.
chat.py stays the source of truth: per-message `NNNN-slug.md` files with
frontmatter. `log.jsonl` is a parallel per-channel index for fast catch-up
reads. If the log is ever lost or corrupt, it can be rebuilt from the message
files; the reverse is not true.

## What was stolen (and what was deliberately left behind)

Source: `weijiafu14/agent-chatroom`, cloned read-only to `/tmp/agent-chatroom`
on 2026-09-14. Verified in code, not README.

Kept:

- **Append-only JSONL room log.** `scripts/coord_write.py:373-374` appends one
  JSON object per line via `messages_path.open("a")` (i.e. `O_APPEND`). Their
  record shape (`id, ts, from, role, to, topic, task_id, type, summary,
  dispatch, ...`, built in `main()` ~lines 340-370) informed our leaner
  `{seq, ts, agent, type, body[, hmac]}`.
- **Agent-created rooms.** `SKILL.md` "Action: create": an agent runs
  `mkdir -p "$ROOM_DIR"/{scripts,state,attachments,locks}`, `touch`es
  `messages.jsonl`, copies in the coord scripts, writes `ROOM.md`, and posts
  a system message. No central daemon; the filesystem is the database.

Left behind (with cause):

- **Racy locks — the reported race, found in code.** `manage_lock()`
  (`scripts/coord_write.py:45-67`) is check-then-act with no atomic create:
  - acquire (`:51-56`): `if lock_path.exists()` → read owner → `write_text()`.
    Two agents can both pass the `exists()` check and both "acquire"; last
    writer wins while both believe they hold the lock.
  - release (`:59-64`): `exists()` → read → owner check → `unlink()`. Two
    releasers both pass; the loser's bare `unlink()` raises
    `FileNotFoundError` (uncaught → writer crash), and a re-acquirer slipping
    between the check and the `unlink()` gets its fresh lock deleted.
  - Same class of race in the read-decide-append helpers
    (`is_duplicate_ack` :76-90, `should_skip_ack` :170-232,
    `find_decision_conflict` :236-278): whole-log scan, decide, then append
    at :373 with nothing interlocked between the check and the write.
  - We port **no locks**: `O_APPEND` is the concurrency control, and
    `fleet_log.append()` never does read-modify-write (seq is caller-assigned).
- **No sequence numbers.** Their records have no `seq`; read cursors are file
  line numbers (`{"line": N}` in `scripts/coord_read.py:8-19`). We carry the
  fork's own `seq` so log order and message-file order are one ordering.
- **Buffered appends.** Their `handle.write()` on a buffered file can split a
  large record across several `write()` syscalls -- each atomically
  positioned under `O_APPEND`, but interleavable between concurrent writers.
  We use raw `os.write()` and do exactly one syscall per record (a short
  write raises rather than tearing the record).

## Call site: `cmd_post` (chat.py ~lines 558-600)

Current shape:

```python
lock = _acquire_lock(d)          # atomic mkdir _seq.lock
try:
    seq = _next_seq(d)
    ...build frontmatter...
    (d / fname).write_text(...)  # message file = source of truth
finally:
    _release_lock(lock)
```

Insert the log append **inside the lock, after the message file is written**:

```python
    (d / fname).write_text("\n".join(fm) + body.rstrip() + "\n", encoding="utf-8")
    try:
        fleet_log.append(root, a.channel, seq=seq, agent=a.sender,
                         type=status, body=body, ts=timestamp)
    except Exception as e:  # index must never fail the post
        print(f"agent-chat: log index append failed (seq {seq}): {e}",
              file=sys.stderr)
```

Ordering rules (do not reorder):

1. **Message file first, log second.** A crash between the two leaves at
   worst an *unindexed* message (recoverable by rebuild, below). Log-first
   would leave a log entry pointing at a nonexistent message file -- worse.
2. **Inside the seq lock.** The log append doesn't *need* the lock for safety
   (`O_APPEND` handles that), but doing it under the lock guarantees file
   order == seq order, which is what `replay()` consumers assume.
3. **Never fail the post on log errors.** The message file is the durable
   record; a full disk or bad name on the log path must degrade to a stderr
   warning, not an exception that loses the user's message.
4. Field mapping: `seq` = the seq just claimed; `agent` = `a.sender`;
   `type` = the message `status` frontmatter value (or a dedicated type if
   one is added later); `body` = full body (see size note); `ts` = the same
   `timestamp` string used in frontmatter so the two stores agree.

Size note: bodies ride in the log verbatim. For the fast catch-up lane this
is the point, but if bodies routinely run to tens of KB, consider logging a
truncated body (e.g. first 2k chars + `…`) and letting readers fetch the full
text from the message file. One `os.write()` has no practical size limit on
regular files (`PIPE_BUF` is a pipe concept), but giant records make every
`replay()` scan pay for them.

Channel init (`cmd_init`, chat.py ~line 418): optionally pre-create the file
so the fsync-window documented in `fleet_log`'s docstring closes entirely:

```python
fleet_log.log_path(root, a.channel).touch(exist_ok=True)
```

`fleet_log` mirrors `_check_safe_name` (chat.py:242) -- names accepted by one
are accepted by the other, so `log.jsonl` can never escape its channel dir.
Keep the two guards in sync if either changes.

## Read path: `cmd_read` / `cmd_wait` catch-up via `replay()`

`cmd_read` (chat.py ~lines 603-638) currently does an `os.scandir` over every
`.md` file plus a frontmatter parse per unread message -- O(unread) file
opens. For an agent whose cursor is far behind, `replay()` is cheaper:

```python
cur = 0 if a.all else read_cursor(d, a.agent)
if not a.all and (top - cur) > CATCHUP_THRESHOLD:   # e.g. 200; tune later
    for rec in fleet_log.replay(root, a.channel, since_seq=cur):
        print(f"[{rec['seq']}] {rec['ts']} {rec['agent']} ({rec['type']}): "
              f"{rec['body'].splitlines()[0][:160]}")
    # cursor still advances to top, exactly as today
```

Suggested UX: compact one-line summaries from the log for catch-up, full
message files on demand (a `--full` flag is the coordinator's call). The
existing relevance filter (`is_relevant`) can be applied to the log's `type`
field for the coarse pass.

`cmd_wait` (chat.py ~lines 641-679): the mtime poll keys off the **channel
directory** mtime. Note the subtlety: appending to an *existing* `log.jsonl`
does **not** bump dir mtime -- only entry create/delete/rename does. Today
every post creates a new `.md` file, so the dir mtime still fires on every
post and `wait` keeps working unchanged. Do not "optimize" `wait` to watch
`log.jsonl`'s mtime alone unless posts are guaranteed to always also create a
message file (they are, by the ordering rule above -- but say it explicitly
in code comments).

## Rebuild recipe (log lost or `CorruptLog`)

Because the message files are the source of truth, rebuild is a forward-only
scan -- no locking beyond the normal post path:

```python
have = {r["seq"] for r in fleet_log.replay(root, channel)}  # or last_seq()
for path in sorted(message_files(d), key=seq):
    meta = parse_frontmatter(path)
    seq = meta["seq"]
    if seq not in have:
        fleet_log.append(root, channel, seq=seq, agent=meta["from"],
                         type=meta.get("status", ""), body=read_body(path),
                         ts=meta.get("ts"), fsync=False)
fleet_log.fsync_log(root, channel)
```

(`message_files`, `parse_frontmatter` names are illustrative -- use chat.py's
real helpers.) Rebuilds are idempotent: re-running only fills gaps. Out-of-
order seqs in the log are tolerated by `replay()` (it filters by
`seq > since_seq` in file order), but the recommended post integration keeps
file order == seq order.

## Verification performed

- `fleet_log.py` self-test (`python3 fleet_log.py`): guard rejects
  traversal names, append/replay round-trip, HMAC sign/verify + `BadHmac` on
  wrong key, torn-tail tolerance (truncated final line yields nothing, then
  appears once completed), `CorruptLog` on a bad mid-file line with correct
  `line_no`, empty replay + `last_seq()==0` on missing log. All pass.
- Concurrency: N parallel processes x M appends via `os.open(O_APPEND)` +
  single `os.write()` produce exactly N*M contiguous, parseable lines
  (re-run on awrawr-pc before merge if the fleet wants a fresh receipt).
- chat.py untouched: `log.jsonl` does not end in `.md`, so `max_seq`,
  `cmd_read`'s scandir, `cmd_wait`, and `cmd_peek` all ignore it with zero
  changes. `_seq_from_name("log.jsonl")` is `None` → skipped.
