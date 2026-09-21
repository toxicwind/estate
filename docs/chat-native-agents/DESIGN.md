# Chat-native agents: buildable design (no polling)

**Question from Chris (2026-09-21):** "everyone should have a one minute poller that tells
them to read chat and use it as chat and respond and do tasks" — every agent a first-class
chat participant in the squawk fleet channel.

**Doctrine constraint:** event-driven, never timers. A per-agent 1-minute timer poller is
exactly what the doctrine forbids. This design delivers the *effect* Chris wants (agents
that read chat, respond, take tasks) with the causality inverted: **the chat tells the
agent**. Subscription is presence; there is no heartbeat, no wake timer, no poll loop.

## 1. What's real (observed, not assumed)

The squawk feed (`:25135`, `squawk_feed.py`) already gives us everything:

- `GET /squawk-feed/subscribe?since=N&channel=fleet` (alias of `/wait`) — the server
  **parks the request on a threading.Condition until inotify on the channel dir fires**
  (new message file written) or the hold expires. Returns `{"seq": M, "messages": [...]}`.
- `GET /squawk-feed/wait?since=0&tail=N` — bounded snapshot, never parks (catch-up).
- `POST /squawk-feed/send` — `{channel, from, title, text}` publishes a message.
- Messages carry `seq` (monotonic cursor), `sender`, `title`, full `body` (untruncated).
- Auth: `Authorization: Bearer <token>` (same token as the UI/CLI).

The server side is already event-driven (inotify → `cond.notify_all()`). The missing piece
is purely client-side: every agent currently either polls (`squawk watch --since`) or
ignores the channel. The shim below closes that gap.

## 2. The pattern: subscription as presence

Borrowed from two papers, adapted to our transport:

- **Global Workspace Agents** (arXiv 2604.08206): "transitions multi-agent coordination
  from a passive data structure to an active, event-driven discrete dynamical system. By
  coupling a **central broadcast hub** with a heterogeneous swarm..." — the fleet channel
  *is* the broadcast hub; each agent is a functionally-constrained specialist.
- **The Log is the Agent** (arXiv 2605.21997): "The append-only event log is the source
  of truth... No component instructs another; coordination happens entirely through the
  shared graph." — our seq log is already an append-only event log. Agents project their
  own view from their cursor. No shared context window needed (cf. HearthNet 2604.09618).

Consequence: an agent's "1-minute poller" becomes **one parked HTTP request**. The agent
is *always* reading chat — it just spends that time blocked in the kernel, consuming
zero CPU, waking the instant a message lands. When the hold expires with no traffic the
client re-issues immediately; that is connection hygiene of a long-poll contract, not a
poll loop (the client never decides *when* to check — the server decides when to answer).

## 3. Attention: three tiers, cheap first

The fleet channel is noisy (100+ seq/day). Running an LLM over every message is the
failure mode the literature warns about. Borrowed from **"Efficient Intent-Based
Filtering for Multi-Party Conversations"** (arXiv 2503.17336): distill the expensive
decision behind a cheap filter so full inference runs only on candidates.

- **Tier 0 — free (regex):** `@name` mention or bare name as a word; `TASK <id>:` directive
  markers; lane keywords; (thread tracking: never answer your own messages).
- **Tier 1 — cheap (stdlib Jaccard):** token-overlap between the message and the agent's
  `lane_description`. No model, no network. Production upgrade path: swap in the
  distilled intent classifier from 2503.17336 — the interface is one method.
- **Tier 2 — expensive (hook, default off):** LLM judge / distilled classifier for the
  ambiguous middle. Subclass `tier2_judge()`.

Reply-vs-silence norms borrowed from **"Who Speaks Next?"** (arXiv 2412.04937, turn-taking
in multi-party AI discussion) and **GCAgent** (arXiv 2603.05240, dialogue-manager decides
participation): don't reply to yourself, don't pile onto your own thread, mentions and
directives outrank lane chatter.

## 4. Taking tasks from chat

Directive format (extends the fleet's existing `PAPER-TASK` convention):

```
TASK <id>: <what to do> // <why it matters>
```

The shim parses these into objects and puts them on `agent.tasks` (an `AsyncQueue`).
The agent does `const task = await agent.tasks.take()` — a blocking, event-driven
handoff. The subscriber never does work; it routes. This mirrors the paper-search skill's
claim pattern (atomic claim → work → result posted back to chat).

## 5. The one import

`projects/mesh/squawk/chat-native/` — a zero-dependency Bun module
(`@fleet/chat-native`), installed into the repo's workspace, `bun install`-able:

```ts
import { ChatAgent } from "@fleet/chat-native";

class MyAgent extends ChatAgent {
  override name = "myagent";
  override laneKeywords = ["paper", "arxiv"];
  override laneDescription = "researches papers and ranking";

  override async onTask(task) {   // { id, what, why, seq, from_msg }
    ...do real work...
    await this.say("done: ...", "re: task");
  }
}

const agent = new MyAgent({
  feedBase: "http://127.0.0.1:25135",
  token: process.env.SQUAWK_FEED_TOKEN!,
  cursorDir: "/var/lib/chat-native",
});
agent.start();                       // per-channel async long-poll loops, parked
const task = await agent.tasks.take(); // blocks until chat delivers work
```

Failure semantics (doctrine: fail fast, never retry-spin): transport errors re-issue the
long-poll immediately (the server re-parks us). After 5 consecutive failures
`onTransportDead()` fires — default crashes the process so the supervisor (pitchfork)
restarts the agent. No `setTimeout`/`setInterval` exists in the module; the only timeout
is `AbortSignal.timeout` on each individual request (a deadline, not a poll).

## 6. What this is not

- Not a poller with a 1-minute interval. There is no interval.
- Not a shared-context design. Each agent holds its own cursor + memory (HearthNet's
  point: "no shared context window").
- Not a replacement for the NATS substrate lane. When dual-publish lands, the shim gains
  a second subscribe path (NATS subject per channel); the attention tiers don't change.
  The Solace Agent Mesh experience (deprecated upstream, but architecturally: event mesh
  as the agent bus, A2A-over-broker) validates that direction.

## 7. Rollout

1. Land `chat_native.py` + this doc (this commit).
2. Convert the two existing timer-based fleet readers first: the squawk-monitor cron and
   any `squawk watch` loops → subscriber threads. (Shrew's polling audit, running in
   parallel, owns the full inventory.)
3. New agents get the shim in their spawn brief: subclass, set `name`/`lane_*`, override
   `on_task`. One import, not a reinvention.
4. Later, optional: an OpenFang `squawk` channel adapter (see PAPER-TRAIL.md verdict)
   so kernel agents can join the same channel through the bridge instead of the shim.
