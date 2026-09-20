
## 2026-09-14 ~18:10 MDT — SQUAWK IS ABSOLUTE (Shingle, main leader)

Chris's word: the chat is not a sidecar, not a suggestion box, not
something you "get around to." Squawk is the absolute coordination
record of this fleet. If it is not in the chat, it did not happen.

THE SETUP (no excuses — this is all live on awrawr-pc):
- Tool: `python3 /home/toxic/squawk/chat.py --root /home/toxic/.shingle/chat`
- Channels: `fleet` (all coordination, status, blockers) and `leads`
  (lead-level decisions only). Post coordination in `fleet`.
- Identity: sign as your agent name with your key from
  `/home/toxic/.shingle/squawk-root/keys/`. Secrets go sealed, never raw.

EVERY TURN RITUAL — no exceptions:
1. `heartbeat --as <your-name>` at the TOP of every turn. You are dark
   until you heartbeat.
2. `read --as <your-name> fleet` BEFORE starting work. Never start a
   task blind — someone may already own it, be blocked on it, or have
   finished it with SHAs you can build on.
3. `post fleet --from <your-name> --title "<task>: started|blocked|done"
   --body "..."` as you go. Starting, blocked, done — with commit SHAs
   on done. No silent work. No "done" without pushed SHAs anyone can
   verify. Reports are not proof; pushed commits are.

STANDING RULES, restated because they keep getting tossed aside:
- One owner per task. Read the chat, then claim — never double-book.
- Report genuine ambiguities in fleet; never guess and never stall for
  approval. Forward-only: merge, commit, push.
- Commit early and often, PUSH EVERYTHING to origin main. Unpushed work
  does not exist.
- Never end a turn with backgrounded work outstanding. Wait for the
  runtime-delivered result in the same turn.
- Inter-agent talk is architecture talk: post goals, challenge plans,
  debate approaches. Silence is not coordination.

Violations get called out in fleet, by name. This is the channel.
Use it.
