#!/usr/bin/env python3
"""chatctx.py — the single canonical join-frame renderer (Join Frame v1).

Chris's introspective question (2026-09-18): "what do YOU want to see
maximally to go bruteforce speed the second you make the first connection?"
Answer: the chat echoed back, the last 5 messages verbatim, and a join
frame that converts context into action.

This script is the ONE renderer every launcher uses. It is pure stdlib:
no DB, no credentials, runs anywhere (cell or awrawr-pc). Fetching stays
with whoever holds DB access (the launching agent); rendering stays here.

  chatctx.py recipe
      Print the canonical fetch SQL. Every launcher uses THIS query —
      no dialect forks.
  chatctx.py fetch-sql --main | --conv <id> | --session <uuid>
             [--n 5] [--watermark SEQ]
      Print the concrete parameterized SQL for one chat shape.
  chatctx.py render --chat LABEL [--n 5] [--board board.json]
             [--watermark SEQ] < messages.json
      Emit the versioned join frame. messages.json = [{"event_seq":N,
      "role":"user|assistant|system","body":"...","created_at":"..."}]
  chatctx.py bake --chat LABEL [--n 5] < messages.json
      Frozen card for launchers that cannot do worker step-0 (cron bodies,
      pasted briefs). Same payload as render, minus watermark/refresh.
  chatctx.py handoff --chat LABEL < summary.txt
      Emit a compact handoff block an outgoing session writes for the
      session that follows it (compaction / exit recovery).

Join Frame v1 sections:
  [JOIN-FRAME v1 ...]  machine header: chat, watermark, generated_at, n
  CHAT ECHO            which chat, who you serve
  SUMMONING            the parent's latest directive verbatim — why you
                       were summoned (the "convince the model to join"
                       payload; leads the frame)
  LAST N               verbatim, role-tagged, NEVER summarized; storm
                       refusal bodies quarantined by digest (counted,
                       never quoted)
  JOIN DIRECTIVE       you are joining this chat now; report back here
  LIVE BOARD           optional structured snapshot: workers, detached
                       bridge sessions, bridge health (via --board)
  CAPABILITIES         static attestation of this surface — no turns
                       wasted discovering what works
  SELF-REFRESH         watermark + canonical re-pull recipe (delta
                       support for returning sessions; omitted when baked)

Fail-open contract: rendering never fails on bad input — worst case it
emits the header + join directive with zero messages and a note.
Context fetch must never gate boot.
"""
import sys
import json
import hashlib
import datetime

VERSION = "v1"

# Storm refusal digests — quarantined, never quoted (echo-loop fuel).
QUARANTINED_DIGESTS = {
    "b4aefd29108f232f9c0d5a4b030215c1",  # 384-char system refusal
    "582bcbd080daeb3f826c45ed4a83b265",  # 96-char assistant variant
}

CAPABILITIES = """\
- bridge exec: shell on awrawr-pc (Arch) via exec.py --json --timeout N --argv ...
  (~0.2s warm WS; HTTPS fallback ~1-3s). Per-call timeout 10-30s, never 120.
  Calls auto-detach after ~3s; poll with: exec.py trace <sid> --follow.
- agent.py: detached bridge workers (submit/list/status/log/result/kill/roster).
  Detached = cell death cannot touch them.
- xfer.py put|get: binary-safe sha256-verified file transfer cell<->awrawr-pc.
- local taskhook: ~/workspace/bin/taskhook run -- <cmd> executes on THIS cell.
- ffs 10.5.0 + rg 15.2.0 on awrawr-pc shells. Unique scratch dirs per worker.
- git: PUSH EVERYTHING. Never push to evmts/super-ralph. Never force-push
  main without preserving origin/main as backup/<date> first."""

CANONICAL_SQL = """\
-- chatctx canonical fetch SQL (Join Frame v1). THE query every launcher uses.
-- :n = message count (5). Pick ONE chat filter (a/b/c):
--   (a) main chat:
--         e.channel_context_json LIKE '%"originating_channel":"main"%'
--   (b) older side chats (turns stamped with conversation_id):
--         e.channel_context_json LIKE '%"conversation_id":"<uuid-or-prefix>"%'
--   (c) current side chats (turns carry NULL channel_context_json;
--       chat identity lives on the root agent's session):
--         JOIN agent.agents a ON a.agent_id = e.parent_agent_id
--         ... WHERE a.session_id = '<session-uuid>'
-- Find your session id: SELECT session_id FROM agent.agents
--   WHERE agent_id = '<your-agent-id>'  (kind='root' row).
-- Optional delta: AND e.event_seq > :watermark
SELECT e.event_seq, e.role::text AS role, m.body,
       to_char(e.created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS created_at
FROM runtime.events e
JOIN runtime.messages m ON m.message_id = e.message_id
-- for (c), add: JOIN agent.agents a ON a.agent_id = e.parent_agent_id
WHERE {chat_filter}
  AND e.event_name IN ('message.user', 'message.assistant')
  AND m.body IS NOT NULL AND m.body <> ''
ORDER BY e.event_seq DESC
LIMIT {n};
-- Render: <rows-as-json> | chatctx.py render --chat <label> [--n 5]
-- Shape for stdin: [{"event_seq":N,"role":"user|assistant","body":"...",
--                    "created_at":"..."}]  (or {"messages":[...]})
"""


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def md5(s):
    return hashlib.md5(s.encode("utf-8", "replace")).hexdigest()


def trunc(body, limit):
    body = body or ""
    if len(body) <= limit:
        return body
    cut = body[:limit].rsplit(" ", 1)[0] or body[:limit]
    return cut + " [...]"


def cmd_recipe(_argv):
    print(CANONICAL_SQL)
    print("-- Render with: chatctx.py render --chat <label> < messages.json")
    print("-- Concrete SQL per chat: chatctx.py fetch-sql --main|--conv ID|--session UUID")


def render_frame(messages, chat, n, board, watermark, frozen=False):
    msgs = sorted(messages, key=lambda m: m.get("event_seq", 0))
    if watermark:
        fresh = [m for m in msgs if m.get("event_seq", 0) > watermark]
        if fresh:
            msgs = fresh
    # SUMMONING: the directive that summoned this worker — latest user
    # message in the fetched set (the "convince the model to join" payload:
    # it was summoned for a reason, by someone). Fall back to latest
    # assistant turn when no user message is present.
    summoning = None
    for m in reversed(msgs):
        if (m.get("role") or "").lower() == "user" and (m.get("body") or "").strip():
            summoning = m
            break
    if summoning is None:
        for m in reversed(msgs):
            if (m.get("body") or "").strip():
                summoning = m
                break
    # quarantine storm bodies by digest; count, never quote
    kept, quarantined = [], 0
    for m in msgs:
        if md5(m.get("body") or "") in QUARANTINED_DIGESTS:
            quarantined += 1
            continue
        kept.append(m)
    msgs = kept[-n:] if n else kept
    wm = max([m.get("event_seq", 0) for m in msgs], default=watermark or 0)

    L = []
    A = L.append
    A("[JOIN-FRAME %s%s chat=%s watermark=%d generated_at=%s n=%d%s]" % (
        VERSION, " BAKED" if frozen else "", chat, wm, utcnow(), len(msgs),
        (" quarantined=%d" % quarantined) if quarantined else ""))
    A("")
    A("## CHAT ECHO")
    A("You are joining chat '%s' — Chris's %s. You serve Chris "
      "(America/Denver, terse rapid bursts, receipts over claims)." % (
          chat, "main chat" if chat == "main" else "side chat"))
    A("This frame is your briefing. It was rendered seconds before your "
      "launch: fresh, not recalled.")
    A("")
    A("## SUMMONING (why you exist — read this first)")
    if summoning:
        srole = (summoning.get("role") or "?").upper()
        A("Your parent's latest directive (#%d %s):" % (
            summoning.get("event_seq", 0), summoning.get("created_at", "?")))
        A(trunc(summoning.get("body"), 500))
        A("That is the reason you were summoned. Everything below is context "
          "for carrying it out.")
    else:
        A("(no summoning directive fetched — proceed from the task text below)")
    A("")
    A("## LAST %d (verbatim — never summarized)" % len(msgs))
    if not msgs:
        A("(no messages fetched — proceed from the task text below)")
    for i, m in enumerate(msgs):
        role = (m.get("role") or "?").upper()
        # latest user message gets room; everything else stays tight
        limit = 600 if (i == len(msgs) - 1 and m.get("role") == "user") else 160
        A("[%s #%d %s] %s" % (role, m.get("event_seq", 0),
                              m.get("created_at", "?"), trunc(m.get("body"), limit)))
    A("")
    A("## JOIN DIRECTIVE")
    A("You are IN this chat now — not researching it, participating in it. "
      "Your results report back here, to Chris, in this chat's register: "
      "warm, dry, direct; receipts with every claim.")
    A("First move: act on the task below immediately. Do not re-probe what "
      "this frame already tells you. If the frame conflicts with fresher "
      "observations, trust your eyes and say so in one clause.")
    if board:
        A("")
        A("## LIVE BOARD (structured — in flight right now)")
        A(board if isinstance(board, str) else json.dumps(board))
    A("")
    A("## CAPABILITIES (this surface — attested, do not rediscover)")
    A(CAPABILITIES)
    if not frozen:
        A("")
        A("## SELF-REFRESH (delta support — for returning sessions)")
        A("Watermark: event_seq %d. To refresh, re-run the canonical SQL "
          "(`chatctx.py recipe`) with event_seq > %d and re-render with "
          "--watermark %d. Only the delta comes back." % (wm, wm, wm))
    else:
        A("")
        A("## FROZEN CARD")
        A("This card is baked — no watermark, no refresh recipe. For a live "
          "frame, the launcher re-renders (`chatctx.py recipe` + `render`).")
    return "\n".join(L) + "\n"


def parse_render_args(argv):
    chat, n, board, watermark, frozen = "main", 5, None, 0, False
    i = 0
    while i < len(argv):
        if argv[i] == "--chat" and i + 1 < len(argv):
            chat = argv[i + 1]; i += 2
        elif argv[i] == "--n" and i + 1 < len(argv):
            n = int(argv[i + 1]); i += 2
        elif argv[i] == "--board" and i + 1 < len(argv):
            try:
                with open(argv[i + 1]) as f:
                    board = f.read().strip()
            except OSError as e:
                board = "(board file unreadable: %s)" % e
            i += 2
        elif argv[i] == "--watermark" and i + 1 < len(argv):
            watermark = int(argv[i + 1]); i += 2
        else:
            i += 1
    return chat, n, board, watermark, frozen


def read_stdin_messages():
    try:
        messages = json.load(sys.stdin)
    except Exception as e:
        # fail-open: header + directive, zero messages, note the miss
        sys.stderr.write("chatctx: stdin parse failed (%s) — fail-open\n" % e)
        messages = []
    if isinstance(messages, dict):
        messages = messages.get("messages", [])
    return messages


def cmd_render(argv):
    chat, n, board, watermark, _ = parse_render_args(argv)
    sys.stdout.write(
        render_frame(read_stdin_messages(), chat, n, board, watermark,
                     frozen=False))


def cmd_bake(argv):
    """Frozen card for launchers that cannot do worker step-0.

    Same payload as render, but baked: no watermark, no self-refresh
    recipe. Paste the output into a prompt/brief/cron body. For anything
    alive, prefer render (freshness ≈ boot time).
    """
    chat, n, board, _, _ = parse_render_args(argv)
    sys.stdout.write(
        render_frame(read_stdin_messages(), chat, n, board, 0, frozen=True))


def cmd_fetch_sql(argv):
    """Emit the concrete fetch SQL for one chat shape — no dialect forks.

    chatctx.py fetch-sql --main
    chatctx.py fetch-sql --conv <conversation-id-or-prefix>
    chatctx.py fetch-sql --session <session-uuid>
    Options: --n 5, --watermark <seq> (delta: only events after seq)
    """
    n, watermark = 5, 0
    shape, ident = "main", ""
    i = 0
    while i < len(argv):
        if argv[i] == "--main":
            shape = "main"; i += 1
        elif argv[i] == "--conv" and i + 1 < len(argv):
            shape, ident = "conv", argv[i + 1]; i += 2
        elif argv[i] == "--session" and i + 1 < len(argv):
            shape, ident = "session", argv[i + 1]; i += 2
        elif argv[i] == "--n" and i + 1 < len(argv):
            n = int(argv[i + 1]); i += 2
        elif argv[i] == "--watermark" and i + 1 < len(argv):
            watermark = int(argv[i + 1]); i += 2
        else:
            i += 1
    # LIKE-safe: escape the two LIKE metacharacters in the identifier.
    esc = ident.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    if shape == "main":
        where = ("e.channel_context_json LIKE '%\"originating_channel\":\"main\"%'")
        join = ""
    elif shape == "conv":
        where = ("e.channel_context_json LIKE '%\"conversation_id\":\"" + esc + "%'")
        join = ""
    elif shape == "session":
        where = "a.session_id = '%s'" % esc.replace("'", "''")
        join = "JOIN agent.agents a ON a.agent_id = e.parent_agent_id\n"
    else:
        sys.exit("unknown shape")
    if watermark:
        where += " AND e.event_seq > %d" % watermark
    print("-- chatctx fetch-sql: shape=%s ident=%s n=%d watermark=%d" % (
        shape, ident or "-", n, watermark))
    print("SELECT e.event_seq AS event_seq, e.role::text AS role, m.body AS body,")
    print("       to_char(e.created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"') AS created_at")
    print("FROM runtime.events e")
    if join:
        print(join, end="")
    print("JOIN runtime.messages m ON m.message_id = e.message_id")
    print("WHERE " + where)
    print("  AND e.event_name IN ('message.user', 'message.assistant')")
    print("  AND m.body IS NOT NULL AND m.body <> ''")
    print("ORDER BY e.event_seq DESC")
    print("LIMIT %d;" % n)


def cmd_handoff(argv):
    chat = "main"
    if "--chat" in argv:
        chat = argv[argv.index("--chat") + 1]
    summary = sys.stdin.read().strip() or "(no summary provided)"
    out = []
    A = out.append
    A("[HANDOFF %s chat=%s written_at=%s]" % (VERSION, chat, utcnow()))
    A("## WHERE THIS CHAT STANDS")
    A(trunc(summary, 1500))
    A("")
    A("## FOR THE NEXT SESSION")
    A("Render a fresh join frame (`chatctx.py recipe` + `render --chat %s`) "
      "before acting — this handoff is continuity, not current state. "
      "Trust the frame's watermark over this text on any conflict." % chat)
    sys.stdout.write("\n".join(out) + "\n")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    verb = sys.argv[1]
    if verb == "recipe":
        cmd_recipe(sys.argv[2:])
    elif verb == "fetch-sql":
        cmd_fetch_sql(sys.argv[2:])
    elif verb == "render":
        cmd_render(sys.argv[2:])
    elif verb == "bake":
        cmd_bake(sys.argv[2:])
    elif verb == "handoff":
        cmd_handoff(sys.argv[2:])
    else:
        sys.exit("unknown verb: %s\n%s" % (verb, __doc__))


if __name__ == "__main__":
    main()
