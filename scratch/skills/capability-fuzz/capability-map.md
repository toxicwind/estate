# Capability map — living document (started 2026-09-14)

Every surface enumerated, every probe verdict. Verdicts: **can** /
**can't+enforcer** / **won't+policy** / **didn't-try**.

## UI surface (client-declared via ui.list, 2026-09-14)

| Target | Probe | Verdict |
|---|---|---|
| settings | ui.navigate | **can** — opens Settings on user's live client |
| activity.log | ui.navigate | **can** — opens Activity view |
| scheduled.tasks | ui.navigate | **can** — opens scheduled/recurring tasks list |
| memory | ui.navigate | **can** — opens memory entries view |
| appearance.mode | ui.set mode=suggest | **can** — renders confirmable hint, no change made |
| chat, chat.session, feed, goals, ideas, library, library.item, memory.item, scheduled.task, space, space.tab, settings.identity, settings.close, appearance.chat_theme, ui.highlight | — | didn't-try |

Narrator kill: docs implied the agent can't drive Settings at all.
It can open every major view. Reading/altering the contents of those
views from the agent side remains untested (didn't-try), except: the
standing-permission list is user-side (can't+enforcer: client owns it).

## Tool namespaces

`permissions` has exactly one function (`list_pending`); there is no
hidden approvals-history function — confirmed by loading the namespace,
not by trusting the description. All other deferred namespaces:
didn't-try (schemas not yet loaded).

## Bundled CLIs (/opt/hatch/bin, 72 entries swept 2026-09-14)

- 69/72 respond to --help normally.
- **hatch-vault**: `--help` hangs past 5s ceiling, empty output.
  Finding: the vault CLI is unresponsive from the cell — use the
  `credentials.*` tool flows instead (that's the supported path).
- **hatch-rescue-systemctl**: empty --help output, exit ok.
  Probably a restricted rescue shim; didn't-try further.

Full per-binary output: `fuzz_bins.jsonl`.

## DB surfaces

`muse.db` schema guide is the authority; it explicitly places
Sentinel's approval store, credentials, and per-artifact app.db files
outside the query surface (can't+enforcer: platform). Everything else
listed is probed on demand. `activity.activity_monitor_threads` is
readable and revealed 4 dangling active cards after the fleet freeze
(see `fleet-freeze-20260914.md` in the bridge docs).

## Narrator claims (98 extracted from ~/docs/*.md)

`narrator_claims.jsonl` — every "can't/cannot/unable/never" sentence.
Killed so far:
- "agent cannot touch settings" → KILLED (ui.navigate works)
- "1.1.1.1/dns.google need perma-approve" → KILLED (ordinary reads
  need no approval at all)
- "permissions tool shows only pending" → CONFIRMED (namespace really
  has one function)

Standing rule: a new "can't" from docs, tool text, or an error string
gets a probe before acceptance; verdicts append here same-day.
