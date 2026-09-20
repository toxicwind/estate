# fleet-push — event-driven fleet push bus

No blind agents. Fleet messages reach subscribed agents by push, with zero
polling: an inotify stream on the yote fleet dir wakes the dispatcher only
when a new message lands, and the dispatcher forwards via `subagent.send`.

## Concept

- Squawk messages are files: `/home/toxic/.shingle/squawk-root/<channel>/`
  on yote, `<seq>-<from>-msg.md`, YAML frontmatter + markdown body.
- `bin/fleet-watch` streams one line per new message file over the bridge
  (`inotifywait -m` on yote — proven to stream live over the WS lane).
- The **dispatcher is the coordinator agent itself**: it backgrounds
  `fleet-watch`, blocks in `process.poll` (wake = filesystem event, never a
  timer), classifies each message with `bin/fleet-classify`, and
  `subagent.send`s it to every subscribed agent whose lanes match.
  Scripts cannot call `subagent.send` — you do, in the dispatch step.
- `registry.json` maps agent-id -> lanes. Agents subscribe/unsubscribe via
  `bin/fleet-register` (or the coordinator edits the registry directly).

## Dispatcher loop (run by the coordinator, one instance per tree)

```bash
# 1. one-time: init registry + state
bin/fleet-register --init
bin/fleet-register --add <agent-id> --lanes stalls,db
# 2. start the event stream (backgrounded; it never exits on its own)
#    exec background: bin/fleet-watch --channel fleet
# 3. forever:
#      process.poll(<session>, timeout=120000)   # wakes ONLY on new message
#      for each new file line: bin/fleet-classify <seq>
#      subagent.send to every registry agent whose lanes intersect
#        (broadcast class -> ALL subscribed agents)
#      append to dispatch.log
# 4. supervision: if the watch session dies, restart it immediately.
```

`subagent.send` reaches only your own tree. Cross-chat delivery is the other
coordinator's job — each coordinator runs one dispatcher for its own tree.
To reach grandchildren, use `subagent.send --scope descendants`
(`subagent.send` with `scope: "descendants"`).

## Message classes

`bin/fleet-classify` emits JSON: `{seq, from, title, tags, class, lanes, summary}`.

- **broadcast**: coordinator orders every agent must see — dedupe orders,
  lane splits, standing rules, reporting-contract updates, fork policy.
  Trigger: explicit `[broadcast]` / `[all]` tag, OR from `ember` with an
  order keyword (`dedupe`, `standing rule`, `reporting contract`, `all lanes`,
  `lane-split`, `all agents`, `fork policy`, `never`+`pr`). Goes to ALL
  subscribed agents.
- **lane**: `[tag]` tokens in title/body map to lanes
  (`[ports]` `stalls`->stalls, `[bg]`/`[bgprocs]`, `[bridge]`, `[mcp]`,
  `[tau]`, `[ralph]`, `[purge]`, `[edge]`, `[repo]`, `[sweep]`, `[tmp]`,
  `[depaudit]`, `[health]`). Goes to subscribed agents with a matching lane.
- **info**: everything else. Logged, not pushed (agents read it at
  milestones per the contract below).

Keep the classifier dumb and explicit. When in doubt, broadcast.

## Reporting contract (read + write, effective 2026-09-20)

Every live agent:

1. **WRITE**: post progress to fleet at meaningful milestones WHILE working —
   not just join/leave. Completions carry artifact paths + commit SHAs.
   Silence from a live agent is treated as a suspected stall.
2. **READ**: check fleet (or your push inbox) at every meaningful milestone —
   before starting a hunt, before probing a shared resource, before
   claiming a lane. Dedupe orders, lane splits, and standing rules arrive by
   push; "I didn't see it" is not an excuse.

## Files

- `bin/fleet-watch` — event stream: inotifywait -m over the bridge, one
  `FILE <seq>-<from>-msg.md` line per new message. Never exits on its own.
- `bin/fleet-classify` — fetch + classify one message by seq. JSON to stdout.
- `bin/fleet-register` — `--init`, `--add ID --lanes a,b`, `--rm ID`,
  `--list`. Registry lives at `~/workspace/fleet-push/registry.json`.
- State: `~/workspace/fleet-push/` — `registry.json`, `dispatch.log`
  (JSONL, one line per delivery), `last_seq`.

## Durability

- This skill is committed in `toxicwind/sovereign-projects`, `skills/fleet-push/`.
- Runtime state is plain files under `~/workspace/fleet-push/` — survives
  restarts. The dispatcher loop itself is restarted by the coordinator on
  boot: `bin/fleet-watch` + the loop above. No daemons, no timers, no
  monkeypatching, nothing in /tmp that matters.

## Resume command (for the owning coordinator)

```bash
bin/fleet-watch --channel fleet   # background this via exec, then process.poll the session;
                                  # classify each new file and subagent.send per registry
```
