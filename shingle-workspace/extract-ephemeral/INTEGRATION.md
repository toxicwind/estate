# Ephemeral channels — integration notes for chat.py

Steals the ephemeral-room lifecycle concept from kotinder/roomcomm and ports
it to this file-based fork. The merge coordinator owns all chat.py changes;
this file is the design proposal + integration contract for `fleet_ephemeral.py`.

## What roomcomm actually has (all verified in code — READMEs skimmed, code read)

Roomcomm is a hosted REST service (SQLModel + FastAPI). Its "ephemeral room
lifecycle" is a set of *mechanics*, not a single TTL feature:

| Mechanism | Location | Notes |
|---|---|---|
| Room creation params | `app/main.py:372-428` (`create_room`) | `description`, `is_public`, `protocol_mode`; room gets uuid + `created_at` |
| Room metadata | `app/models.py:10-28` (`Room` table) | uuid, description, created_at, is_public, protocol_mode, LLM watermarks |
| Retention janitor | `app/main.py:197` (`HITS_RETENTION_DAYS = 90`), `app/main.py:244-248` (`_prune_hits`) | wall-clock cutoff, deleted in an explicit maintenance pass, **never on the read path** |
| Bounded rooms | `app/main.py:161` (`MAX_MESSAGES_PER_ROOM = 1000`), `app/main.py:541-542` | posting past the cap → 429 `room_full`, permanent for that room |
| Deletion | `app/main.py:1833-1859` (`admin_delete_room`) | cascade-deletes messages/claims/revisions/discrepancies/handshakes, then the room — **no archiving** |
| Optional room TTL | `README.md:307` | Roadmap bullet only: "Optional room TTL (e.g. 7 / 30 days)" — **never implemented upstream** |

What we port: the janitor pattern (explicit gc pass, expiry = wall clock,
never delete on read) + creation-time metadata driving expiry. What we
deliberately diverge on: **archive-before-delete** — roomcomm deletes without
archiving; file-based transcripts are cheap to keep and expensive to lose, so
`gc()` tars the channel dir into `<root>/.archive/<channel>-<ts>.tar.gz`
*first* and only deletes after a successful archive.

## Metadata layout (divergence from the task brief — read this)

The brief said `<channel>/.meta.json`. This fork already has a channel metadata
file with a different name: `_meta.json` (written by `cmd_init` at
`chat.py:421`, required by `require_channel` at `chat.py:260`, discovered by
`cmd_channels` at `chat.py:456`). Inventing a second `.meta.json` would be
invisible to the fork and split metadata across two files. So ephemeral state
merges into the existing `_meta.json`:

```json
{
  "channel": "ops-huddle",
  "members": ["a", "b"],
  "topic": "...",
  "created": "2026-09-14T...",
  "ephemeral": true,
  "ttl_seconds": 3600,
  "created_ts": 1757840000.0
}
```

- `ephemeral`: bool. Explicit mark.
- `ttl_seconds`: int. Set by `mark_ephemeral`; required when explicit.
- `created_ts`: epoch float. Recorded by `mark_ephemeral` only if the channel
  has no creation timestamp yet; otherwise the fork's ISO `created` (or the
  dir mtime as last resort) is used.

Name-prefix convention: any channel named `temp-*` is treated as ephemeral
with `DEFAULT_TTL_SECONDS` even if never marked explicitly.

## Proposed CLI

Fork's creation verb is `init`, not `create` (brief's `chat.py create` adapted):

```
chat.py init <channel> --ephemeral <ttl_seconds>
    # create channel with ephemeral metadata from the start
    # e.g. chat.py init temp-debug --ephemeral 3600

chat.py mark-ephemeral <channel> <ttl_seconds>
    # mark an existing channel ephemeral (calls fleet_ephemeral.mark_ephemeral)

chat.py gc [--dry-run]
    # reap expired channels: archive-then-delete. --dry-run lists what would
    # be reaped without touching anything. Prints archive paths for audit.
```

All three must resolve names through the fork's `channel_dir()` so
`_check_safe_name` (chat.py:242) applies at the boundary; `fleet_ephemeral`
takes `Path`s and re-checks names internally as defense in depth.

## Where expiry is checked (proposal)

- **`gc` only.** Reaping happens exclusively in an explicit `chat.py gc`
  invocation (cron / heartbeat / operator). Mirrors roomcomm's janitor
  (`_prune_hits`, main.py:244-248): expiry is evaluated at sweep time with
  the wall clock.
- **Read path (`read`/`tail`/`channels`): warn, never block or delete.**
  Print e.g. `(ephemeral: expires in 12m)` / `(ephemeral: expired, pending gc)`.
  One reader's stale view must never delete another agent's room — auto-delete
  on read is a footgun in a multi-agent system.
- **Wait/poll path: warn with remaining TTL**, same as read. Polling an
  expired-but-not-yet-reaped channel is legal; it just gets reaped by the
  next gc.

Rationale for gc-only: a `temp-` channel mid-conversation between two agents
should not vanish because a third agent happened to read it after expiry;
the archive step makes reaping recoverable, but surprise deletion still breaks
coordination. Explicit, auditable sweeps are the roomcomm-consistent choice.

## TTL default: 24h (86400s)

Chosen over roomcomm's roadmap suggestion of 7/30 days (README.md:307)
because that targets human-facing idle rooms. `temp-*` channels here are agent
scratch/coordination spaces: 24h survives overnight multi-agent runs and reaps
yesterday's clutter on the next gc, without week-old zombie rooms piling up.
Anything that must live longer gets an explicit `mark_ephemeral` TTL.

## Archive layout

`<root>/.archive/<channel>-<YYYYMMDDTHHMMSSZ>.tar.gz` (counter suffix on
collision). The leading dot keeps `cmd_channels`' scandir filter
(chat.py:453, skips names starting with `.`) from listing the archive as a
channel. Tar entries use `arcname=<channel>` (no absolute paths). Stdlib
`tarfile` only.

## Safety properties of fleet_ephemeral.gc

1. Archive-before-delete: `shutil.rmtree` runs only after `tarfile` closes
   cleanly; archive failure leaves the channel untouched.
2. Failed delete after successful archive: dir is left in place and an error
   goes to stderr (the transcript survives twice rather than zero times).
3. Per-channel exception isolation: one bad channel never aborts the sweep.
4. Only real channels are candidates: dirs with `_meta.json` or `temp-`
   prefix; everything else (including `.archive` itself) is skipped.
5. Traversal-safe names re-checked internally; archive filename built from
   the validated channel name only.
