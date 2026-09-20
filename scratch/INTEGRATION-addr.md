# fleet_addr.py — integration notes for the merge coordinator

New module: `/home/toxic/.shingle/chat/fleet_addr.py` (106 lines, stdlib only,
smoke-tested on awrawr-pc via `python3 fleet_addr.py`). chat.py was NOT touched.

## What was stolen from madnh/scratchpad (file:line, verified in code)

Upstream: `git clone --depth 1 https://github.com/madnh/scratchpad.git`
(read-only, in /tmp/scratchpad on awrawr-pc). Their turn-taking model was
rejected per brief; only the addressing was ported.

- **Flag**: `cmd/scratchpad/pad.go:322` —
  `f.StringSliceVar(&to, "to", nil, "authors this section is addressed to
  (comma-separated); omit to broadcast...")` on the `post` command.
- **Intent doc**: `cmd/scratchpad/pad.go:249` — "`--to` addresses the section:
  everyone can still READ it, but only those named are woken by
  `pad wait --wake-for me`."
- **Schema**: `internal/pad/pad.go:92` — `To []string \`json:"to,omitempty"\``
  on the section meta. Absent `to` == broadcast.
- **Broadcast**: `internal/pad/pad.go:137` —
  `func (s Section) Broadcast() bool { return len(s.To) == 0 }`.
- **Named match**: `internal/pad/pad.go:140` — `AddressedTo(author)` does exact
  string match of the author against the `to` list.
- **Wake selectors**: `internal/pad/wake.go:44-81` — `ParseWake` accepts
  `any | me | mine | opened | tasks | task:<n>` (union). `wake.go:85` —
  `Wakes(sec, author, w)` evaluates them.
- **"me" semantics**: `internal/pad/wake.go:143` — `concernsAuthor` is true when
  the section is AddressedTo(author), OR replies (`Re`) to a section authored
  by author, OR is a non-task broadcast. Own posts never wake you
  (`wake.go:88-89`): "Your own post is never news to you."

### What scratchpad got right

1. `to` is a **hint, not a lock** — everyone can still read everything; it only
   decides what's worth waking for (pad.go:249).
2. Broadcast is the default (pad.go:137); addressing is opt-in.
3. Wait selectors are a **union** with a safe default (`any`), so narrowing your
   wake never changes default behavior for existing scripts (wake.go:30-32).
4. Filtering never creates a silent gap: sections that wake you are listed along
   with what you missed (pad.go:665-670).

### What scratchpad got wrong (and we don't port)

1. **Turn-taking fights swarm chatter.** Their `post` refuses the author of the
   pad's last message ("not_your_turn", pad.go:246-248) — serializes a medium
   that's meant to be parallel. Rejected outright.
2. **Task ownership overloads `to`.** On task events `--to` stops meaning
   "addressed to" and becomes "task owners" (pad.go:322). One flag, two
   meanings — confusing. Our `to` is addressing only, always.
3. **The `--wake-for me` rules trap** (fixed upstream by always waking on
   rules/continued/notice sections, wake.go:96-113): a narrow selector once
   let an agent keep posting under rules it had never seen. Lesson ported as
   doc rule 4 below: a *hint* layer must never gate *visibility*.

## Semantics decisions for our fork

1. **Broadcast is default (swarm chatter).** Absent `to`, or spellings `""`,
   `"all"`, `"*"`, `"[]` → everyone. Matches chat.py's existing
   `to_list` normalization (chat.py:321-324).
2. **`to` is a hint, not a lock.** It decides wake-worthiness only. `read --all`
   (chat.py:1264) ignores it; nobody is ever prevented from reading.
3. **No turns, no ownership, no "you must respond" state.** Naming an agent
   creates zero obligations and never gates who posts next.
4. **`wait --for-me` semantics**: wake when the message is broadcast OR names
   me, but never on my own posts. This filters *other agents'* directed notes
   out of my wait while keeping the channel's shared chatter. (Mirrors
   scratchpad's `--wake-for me` minus their task selectors.)
5. **Exact, case-sensitive id match** — same as scratchpad's `AddressedTo`
   and chat.py's current `agent in to` (chat.py:334).

## Proposed CLI (coordinator: wire into chat.py)

- `post --to agent1,agent2` — **ALREADY EXISTS** (chat.py:1216,
  `--to` help "recipient agent, or 'all' (default all)"; writes the `to:`
  frontmatter at chat.py:561-576). Consider also accepting it repeatable
  (`action="append"`) for parity with scratchpad's StringSliceVar — optional.
- `wait --for-me` — **NEW FLAG** (store_true). The filtered wait path uses
  `fleet_addr.addressed_wait_filter(meta, agent)`: wake on broadcasts or
  messages naming me, never on my own posts, never on other agents' directed
  notes. Help text suggestion:
  `"only wake on broadcasts or messages addressed to me (skip other agents' directed notes)"`
  Note: today's `cmd_wait` already filters by `is_relevant` (chat.py:666), which
  is equivalent to this gate — so the flag formalizes the current contract.
  If you want scratchpad parity instead (`any` default, `me` as the narrow
  mode — internal/pad/wake.go:30-32), widen default `wait` to wake on every
  new message and let `--for-me` be the narrowing switch. That's a behavior
  change; your call.

## Where the filter plugs in (chat.py file:line)

- `chat.py:327-334` `is_relevant(meta, agent)` — currently
  `meta.get("from") != agent and (not to_list or agent in to_list)`.
  This is exactly `fleet_addr.addressed_wait_filter(fm, agent)` with
  `fm = {"to": meta.get("to", ""), "from": meta.get("from")}`.
  Recommended: delegate `is_relevant` to `addressed_wait_filter` so there's
  one definition of relevance, used by both `read` (chat.py:629-630) and
  `wait` (chat.py:666).
- `chat.py:641-685` `cmd_wait` — add the `--for-me` flag to the argparse at
  chat.py:1270-1282; in the scan loop (chat.py:666), when `a.for_me` is set,
  gate messages with `addressed_wait_filter(meta, a.agent)`.
- `chat.py:291-325` `parse_frontmatter` — already emits `to_list`; no change
  needed. `fleet_addr.parse_recipients` accepts the same raw `to` string and
  yields the same list (verified against chat.py:321-324).

## Compatibility note

`fleet_addr.addressed_wait_filter` ≡ current `chat.py:is_relevant` for all
inputs (same broadcast spellings, same exact-match, same own-post exclusion).
`fleet_addr.is_for_me` is the *pure addressing* predicate (no `from` check) —
useful for inbox-style "was this addressed to me" queries without the wait
semantics.
