# INTEGRATION.md — fleet_tasks.py → chat.py integration proposal

Module landed: `/home/toxic/.shingle/chat/fleet_tasks.py` (new file, no existing files touched).
Source of truth for the atomicity argument: the module docstring + `claim_task()` comments.

This doc proposes (1) the `agent-chat tasks` CLI UX for the merge coordinator to
implement in `chat.py`, and (2) how task events reach the message stream.

Identity note: `fleet_tasks` takes owner/creator strings at face value. The
sibling worker owns agent identity (HMAC); `chat.py` must pass the
*authenticated* agent name as `--owner`/`--by`, never a user-supplied alias.

---

## 1. CLI UX proposal

New top-level subcommand `tasks`, following `chat.py`'s existing conventions
(argparse subparsers like the other `cmd_*`, `--root` flag > `AGENT_CHAT_ROOT`
env > default root, `die()` on errors, `_frontmatter_value` sanitizing):

```
agent-chat tasks create   <channel> "<title>" [--body TEXT|--body-file F] --by AGENT
agent-chat tasks claim    <channel> <task-id> --owner AGENT
agent-chat tasks done     <channel> <task-id> --owner AGENT
agent-chat tasks release  <channel> <task-id> --owner AGENT
agent-chat tasks get      <channel> <task-id>
agent-chat tasks list    <channel> [--status open|claimed|done]
```

Behavior:

- `create` → prints the new task id (short form, e.g. `task-3f9a1c2e04bd` on its
  own line for scripting) and posts a `task_created` stream message (see §2).
  `--body`/`--body-file`/stdin mirror `_read_body()` so long specs can be piped.
- `claim` → prints `claimed: true|false` plus the current holder when false
  (`{"claimed": false, "holder": "agent-07"}` — JSON on stdout keeps it
  machine-readable; a human line on stderr). Exit code 0 either way; the bool
  is the answer, not an error. Posts `task_claimed` message on success.
- `done` → `{"completed": true|false}`; only the owner can complete, so false
  means "you don't hold it / it's not claimed". Posts `task_completed`.
- `release` → `{"released": true|false}`; claimed → open. Posts `task_released`.
- `get` → pretty JSON of the task file.
- `list` → table like `cmd_channels` does:

```
ID                STATUS   OWNER      TITLE
task-3f9a1c2e04bd open     -          rebuild the poller
task-91bd77aa02c1 claimed  agent-07   rotate the kimi tokens
```

`--status` filters; default shows all, sorted by `ts` (fleet_tasks.list_tasks
already sorts).

Error mapping: `TaskNotFound` → `die("task <id> not found in '<channel>'")`;
`FleetTaskError` → `die(str(e))`. Both exit non-zero, message on stderr —
same shape as `AgentChatError` handling elsewhere in `chat.py`.

Implementation sketch for `chat.py` (coordinator-owned):

```python
def cmd_tasks(root, a):
    import fleet_tasks  # sibling module, stdlib-only, no chat.py import (no cycle)
    if a.tasks_cmd == "create":
        task = fleet_tasks.create_task(root, a.channel, a.title, _read_body(a), a.by)
        _announce_task(root, a.channel, "task_created", task["id"], a.by, task["title"])
        print(task["id"])
    elif a.tasks_cmd == "claim":
        ok = fleet_tasks.claim_task(root, a.channel, a.task_id, a.owner)
        ...
```

## 2. Task events in the message stream

Every mutation must also appear as a normal channel message, so agents using
`read`/`wait` (cursor-based) learn about claims without polling `tasks list`.
Reuse the exact `cmd_post` machinery — the message is written with the channel
`_acquire_lock` seq lock (chat.py:339) and gets a real `seq`, so it shows up in
`cmd_read`, `cmd_wait`, cursors, and `roster` counts with zero extra plumbing.

Proposed `_announce_task(root, channel, kind, task_id, actor, title)`:

- Builds the same frontmatter `cmd_post` uses (chat.py:558-595):
  `from: fleet`, `to: all`, `channel: <channel>`, `ts: now_iso()`,
  `status: <kind>` (reuses the existing `status` frontmatter slot —
  `task_created` / `task_claimed` / `task_completed` / `task_released`),
  `title: task <task-id> <verb>`.
- Body templates (one line for the title slug, human-readable body):

  - created:  `🧾 <actor> opened task <task-id>: <title>\nstatus: open — claim with: agent-chat tasks claim <channel> <task-id>`
  - claimed:  `✋ <actor> claimed task <task-id>: <title>\nstatus: open → claimed`
  - completed:`✅ <actor> completed task <task-id>: <title>\nstatus: claimed → done`
  - released: `↩️ <actor> released task <task-id>: <title>\nstatus: claimed → open — claimable again`

- Sender name `fleet`: pick something that sorts/collides with nothing; it is a
  system sender, and `_check_safe_name` on senders is not applied to `from` in
  `cmd_post`, so no conflict. Agents filter with `is_relevant(meta, agent)` —
  `to: all` keeps these visible to everyone, which is what a shared board wants.

Ordering guarantee: mutate the task **first**, announce **second**. The task
file is the source of truth; a failed announcement leaves a true-but-unannounced
task, which is recoverable via `tasks list`. The reverse order could announce a
claim that never landed.

### The `_events.jsonl` outbox (already implemented)

Every mutation also appends one JSON line to `<channel>/tasks/_events.jsonl`
(`ts, kind, task_id, actor, detail`). This is the audit log and the fallback
if announcement is ever skipped:

- A `chat.py tasks sync` (or a tiny watcher loop) can tail it and post any
  un-announced events — dedupe by keeping a `tasks/_events.cursor` file with
  the last-posted line count.
- `dashboard.html`-style UIs can read it without parsing the message stream.

Primary path stays "announce inline at mutation time" (single process, no
divergence); the outbox is the backstop, not the mechanism.

## 3. What the coordinator must NOT do

- Don't reimplement claim logic in `chat.py` — call `fleet_tasks.claim_task()`.
  The atomicity lives in `os.link()` there; any second implementation risks
  getting exclusivity wrong (see module docstring: rename() is NOT exclusive).
- Don't import `fleet_tasks` from `chat.py` at module top if it complicates the
  1608-line file's import graph — a lazy import inside `cmd_tasks` is fine.
- `tasks/` dirs live *inside* the channel dir, so channel deletion semantics
  stay unchanged (deleting a channel deletes its board — document this).

## 4. Verification already done (awrawr-pc, 2026-09-14)

- 20 separate processes, barrier-synchronized, claiming one task: **exactly one
  winner, 3/3 runs** (different winners each run — a real race).
- Lifecycle: idempotent re-claim, non-owner complete blocked, owner complete,
  claim-after-done fails, release → open → re-claimable.
- Error paths: `TaskNotFound` on unknown id, traversal guard rejects
  `../evil` as task id (mirrors chat.py:242).
- Stress script: `/tmp/stress_tasks.py` on awrawr-pc (ephemeral; sources kept at
  `~/workspace/fleet-tasks/stress_tasks.py` in the sandbox).
