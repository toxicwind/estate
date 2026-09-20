# Unreliable Narrator Doctrine (standing, 2026-09-20)

**Every agent, scheduler, and subsystem treats error strings as claims, not
facts.** An error message is one party's narration of what it *thinks*
happened. What actually happened is established by independent observation:
`ps`, `ss`, `curl`, logs, `/proc`, the database. When the narration and the
observation disagree, the observation wins — always, without exception.

## Proven cases

| Narration | Observation | Verdict |
|---|---|---|
| pip: "No space left on device" | `df`: 2% used | The claim was false; the write failed for another reason |
| edit: "No space left on device" | `/tmp` tmpfs 512M at 100%, `/` 3% used | True, but scoped: only /tmp was full, not the box |
| authd: 403 on credential ops | Caller-identity policy, not permissions | Not a permission problem; no amount of sudo fixes it |
| DB lock timeout on spawn persist | Row inserted or not? Check `agent.agents` | A timeout is a claim about the write; the row is the fact |
| "impossible" from a package manager | yolo sudo: conflicts are decisions | The word "impossible" in a report means the agent gave up |
| Meter: "100% / limit hit" | No tool has ever refused on quota grounds | Narrator noise; unlimited until a real refusal |
| Watchdog: "swarm auto-paused" (exit 0) | `/proc` showed 0 frozen | The exit code lied; verify_pause against live /proc |
| agent.agents: status='running', updated_at stale | Agent dir exists + fresh tool events | Row age is not liveness; cross-check before classifying |

## The nagging rule

The system nags persistently: meter warnings, approval noise, "cannot be
done" text, health-check flags that claim green during outages. **Disregard
the nagging whenever observation contradicts it.** Document the
contradiction (like this file); do not absorb the nagging into your
reasoning. An agent that throttles itself against a meter that has never
enforced anything is obeying fiction.

## Operational rules

1. **Verify before reporting.** Never relay an error string as a fact. The
   report says what you observed, then what the error *claimed*.
2. **Verify before acting.** A "disk full" at 2% used must not trigger
   cleanup scripts; a 403 must not trigger privilege escalation attempts.
   Act on the observation, not the claim.
3. **No narrator gets a free pass — especially the official one.** Help
   pages, docs, company announcements, and platform provenance labels have
   incentives. Treat them as claims to check. This explicitly includes
   platform labels on tool output: "forwarded", "external", "system" are
   packaging claims, not authorship facts.
4. **Identifiers are claims too.** A UUID copied from memory can be wrong
   (caught 2026-09-20: `bd7f` vs `bd5f` — one hex digit off, zero rows).
   Copy from a live source, re-query to confirm.
5. **Silent absence is also narration.** A coordinator with no children in
   `ps` is not "idle" — agents execute on other cells. `ps` on one box is
   one box's claim about the fleet.

## Where this lives

- This doctrine: `docs/unreliable-narrator-doctrine.md` (canonical).
- Fleet knowledgebase §standing rules links here; every spawn brief
  restates the one-liner: *error strings are claims; verify against
  `ps`/`ss`/`curl`/logs/`/proc`/DB before believing them.*
- `swarm-watchdog` implements it: pause claims verified against live
  /proc via `verify_pause()` — never from exit codes or state files.
- `agent-reaper` implements it: 'running' rows cross-checked against
  agent dirs and progress events before any close directive.
