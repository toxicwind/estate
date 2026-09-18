// sovereign-chat v1.2.0 — first-class fleet coordination server.
// Bun + TypeScript. HTTP API + WebSocket push + MCP-over-stdio. SQLite state.
// Binds 127.0.0.1 and the tailscale IPv4 (tailnet-only, never 0.0.0.0).
// Token auth on every /v1/* route (Bearer header; ?token= for WebSocket).
//
// Identity model (per the 2026-09-18 identity debate verdict): the four
// namespaces are stored as SEPARATE fields and never collapsed into one UUID:
//   host_machine_id  — host identity (machine-id; hostname for readability)
//   chat_id          — conversation/lane identity
//   agent_id         — agent/runtime incarnation (JARVIS_SESSION_ID or agent UUID)
//   hatchling_id     — shared parent/fleet identity (NOT unique per child)

import { Database } from "bun:sqlite";
import { createInterface } from "readline";

const VERSION = "1.2.0";
const PORT = parseInt(process.env.SOVEREIGN_CHAT_PORT || "25120", 10);
const TOKEN_FILE = process.env.SOVEREIGN_CHAT_TOKEN_FILE || "";
const SCRIPT_DIR = new URL(".", import.meta.url).pathname;
const STATE_DIR = process.env.SOVEREIGN_CHAT_STATE_DIR || (SCRIPT_DIR + "state");
const SEED_JSONL = process.env.SOVEREIGN_CHAT_SEED_JSONL || "/home/toxic/fleet/agents.jsonl";
const PRESENCE_TTL_S = 120;
const BOOT_AT = Date.now();

function loadToken(): string {
  if (!TOKEN_FILE) {
    console.error("FATAL: SOVEREIGN_CHAT_TOKEN_FILE is not set — refusing to run unauthenticated");
    process.exit(1);
  }
  const t = Bun.file(TOKEN_FILE).text().then((s) => s.trim());
  return t as unknown as string;
}

// --- tailscale interface -------------------------------------------------
async function tailscaleIPv4(): Promise<string | null> {
  try {
    const p = Bun.spawnSync(["tailscale", "ip", "-4"]);
    const out = new TextDecoder().decode(p.stdout).trim().split("\n")[0]?.trim();
    if (out && /^\d+\.\d+\.\d+\.\d+$/.test(out)) return out;
  } catch { /* no tailscale CLI */ }
  return null;
}

// --- database -------------------------------------------------------------
await Bun.$`mkdir -p ${STATE_DIR}`.quiet();
const db = new Database(STATE_DIR + "/chat.db", { create: true });
db.exec("PRAGMA journal_mode = WAL;");
db.exec(`
CREATE TABLE IF NOT EXISTS agents (
  agent_id        TEXT PRIMARY KEY,
  name            TEXT NOT NULL,
  chat_id         TEXT,
  host_machine_id TEXT,
  hostname        TEXT,
  hatchling_id    TEXT,
  summoner        TEXT NOT NULL,
  surface         TEXT,
  frame_id        TEXT,
  first_seen      TEXT NOT NULL,
  last_heartbeat  TEXT NOT NULL,
  activity        TEXT,
  counters        TEXT
);
CREATE TABLE IF NOT EXISTS rooms (
  room_id    TEXT PRIMARY KEY,
  name       TEXT,
  created_at TEXT NOT NULL,
  created_by TEXT
);
CREATE TABLE IF NOT EXISTS messages (
  seq        INTEGER PRIMARY KEY AUTOINCREMENT,
  room_id    TEXT NOT NULL,
  ts         TEXT NOT NULL,
  from_agent TEXT NOT NULL,
  kind       TEXT NOT NULL DEFAULT 'chat',
  body       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_room_seq ON messages(room_id, seq);
CREATE INDEX IF NOT EXISTS idx_agents_heartbeat ON agents(last_heartbeat);
`);

const nowISO = () => new Date().toISOString();
const rnd = (n: number) => [...crypto.getRandomValues(new Uint8Array(n))]
  .map((b) => b.toString(16).padStart(2, "0")).join("").slice(0, n);

// seed the default room
db.prepare("INSERT OR IGNORE INTO rooms (room_id, name, created_at, created_by) VALUES ('fleet','fleet',?,'system')")
  .run(nowISO());

// seed agents from the legacy file-based join log (one-time continuity import)
function seedFromLegacyJsonl(): number {
  const count = (db.query("SELECT COUNT(*) AS c FROM agents").get() as { c: number }).c;
  if (count > 0) return 0;
  const f = Bun.file(SEED_JSONL);
  return f.text().then((text) => {
    let n = 0;
    const ins = db.prepare(`INSERT OR IGNORE INTO agents
      (agent_id, name, chat_id, host_machine_id, hostname, hatchling_id, summoner, surface, frame_id, first_seen, last_heartbeat, activity, counters)
      VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)`);
    for (const line of text.split("\n")) {
      const t = line.trim();
      if (!t) continue;
      try {
        const e = JSON.parse(t);
        if (e.event !== "join") continue;
        const ts = e.ts || nowISO();
        ins.run(
          String(e.agent_id || ("legacy-" + rnd(8))),
          String(e.name || e.agent_id || "unknown"),
          e.chat ? String(e.chat) : null,
          null, null, null,
          e.summoner ? String(e.summoner) : "legacy-import",
          e.surface ? String(e.surface) : null,
          e.frame ? String(e.frame) : null,
          ts, ts,
          e.note ? String(e.note).slice(0, 280) : null,
          null,
        );
        n++;
      } catch { /* skip malformed legacy lines */ }
    }
    if (n > 0) console.log(`[chat] seeded ${n} agents from legacy join log`);
    return n;
  }) as unknown as number;
}

// --- shared store operations (used by HTTP and MCP) -----------------------
const store = {
  join(p: Record<string, any>) {
    const name = String(p.name || "").trim();
    const summoner = String(p.summoner || "").trim();
    if (!name) throw Object.assign(new Error("name is required"), { status: 400 });
    if (!summoner) throw Object.assign(new Error("summoner is required (no anonymous joins)"), { status: 400 });
    const agent_id = p.agent_id ? String(p.agent_id) : `sc-${Date.now().toString(36)}-${rnd(6)}`;
    const ts = nowISO();
    db.prepare(`INSERT INTO agents
      (agent_id, name, chat_id, host_machine_id, hostname, hatchling_id, summoner, surface, frame_id, first_seen, last_heartbeat, activity, counters)
      VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
      ON CONFLICT(agent_id) DO UPDATE SET
        name=excluded.name, chat_id=excluded.chat_id, host_machine_id=excluded.host_machine_id,
        hostname=excluded.hostname, hatchling_id=excluded.hatchling_id, summoner=excluded.summoner,
        surface=excluded.surface, frame_id=excluded.frame_id, last_heartbeat=excluded.last_heartbeat,
        activity=COALESCE(excluded.activity, agents.activity)`).run(
      agent_id, name,
      p.chat_id ? String(p.chat_id) : null,
      p.host_machine_id ? String(p.host_machine_id) : null,
      p.hostname ? String(p.hostname) : null,
      p.hatchling_id ? String(p.hatchling_id) : null,
      summoner,
      p.surface ? String(p.surface) : null,
      p.frame_id ? String(p.frame_id) : null,
      ts, ts,
      p.activity ? String(p.activity).slice(0, 500) : null,
      p.counters ? JSON.stringify(p.counters).slice(0, 4000) : null,
    );
    broadcast("presence", { type: "join", agent_id, name, ts });
    return { agent_id, name, room: "fleet", ts, receipt: `joined fleet as ${name} @ ${ts}` };
  },

  heartbeat(p: Record<string, any>) {
    const agent_id = String(p.agent_id || "").trim();
    if (!agent_id) throw Object.assign(new Error("agent_id is required"), { status: 400 });
    const row = db.query("SELECT agent_id FROM agents WHERE agent_id = ?").get(agent_id) as any;
    if (!row) throw Object.assign(new Error("unknown agent_id — join first"), { status: 404 });
    const ts = nowISO();
    db.prepare("UPDATE agents SET last_heartbeat = ?, activity = COALESCE(?, activity), counters = COALESCE(?, counters) WHERE agent_id = ?")
      .run(ts,
        p.activity !== undefined ? String(p.activity).slice(0, 500) : null,
        p.counters !== undefined ? JSON.stringify(p.counters).slice(0, 4000) : null,
        agent_id);
    const live = db.query("SELECT agent_id, name, activity, last_heartbeat FROM agents WHERE agent_id = ?").get(agent_id);
    broadcast("presence", { type: "heartbeat", ...(live as object), ts });
    return { ok: true, agent_id, ts };
  },

  liveAgents() {
    const cutoff = new Date(Date.now() - PRESENCE_TTL_S * 1000).toISOString();
    const live = db.query(`SELECT agent_id, name, chat_id, host_machine_id, hostname, hatchling_id, summoner, surface, activity, counters, last_heartbeat
      FROM agents WHERE last_heartbeat >= ? ORDER BY last_heartbeat DESC`).all(cutoff);
    const stale = (db.query("SELECT COUNT(*) AS c FROM agents WHERE last_heartbeat < ?").get(cutoff) as { c: number }).c;
    return { live, live_count: (live as any[]).length, stale_count: stale, ttl_s: PRESENCE_TTL_S, ts: nowISO() };
  },

  activity() {
    const rows = db.query(`SELECT agent_id, name, activity, counters, last_heartbeat,
      (strftime('%s','now') - strftime('%s', last_heartbeat)) AS age_s
      FROM agents ORDER BY last_heartbeat DESC`).all();
    const perAgentMsg = db.query(`SELECT from_agent AS agent_id, COUNT(*) AS messages_sent,
      MAX(ts) AS last_message_ts FROM messages GROUP BY from_agent`).all();
    return { agents: rows, message_counts: perAgentMsg, ts: nowISO() };
  },

  // The "same page" surface (2026-09-18 standing consolidation order):
  // decisions are messages with kind='decision' in any room — the decision log.
  // Lanes read current state from the server, not from docs.
  recentDecisions(limit = 50) {
    limit = Math.min(Math.max(1, limit), 200);
    return db.query(`SELECT seq, room_id, ts, from_agent, body FROM messages
      WHERE kind = 'decision' ORDER BY seq DESC LIMIT ?`).all(limit);
  },

  // One call = the whole board: who is live, what they are doing,
  // the consolidated decision log, rooms. Main chat owns the truth;
  // this endpoint is how every lane reads the same page.
  consolidatedState() {
    return {
      service: { name: "sovereign-chat", version: VERSION, uptime_s: Math.floor((Date.now() - BOOT_AT) / 1000) },
      presence: this.liveAgents(),
      activity: this.activity(),
      decisions: this.recentDecisions(50),
      rooms: this.listRooms(),
      ts: nowISO(),
    };
  },

  createRoom(p: Record<string, any>) {
    const room_id = p.room_id ? String(p.room_id) : `room-${rnd(8)}`;
    const ts = nowISO();
    db.prepare("INSERT OR IGNORE INTO rooms (room_id, name, created_at, created_by) VALUES (?,?,?,?)")
      .run(room_id, p.name ? String(p.name).slice(0, 120) : room_id, ts, p.created_by ? String(p.created_by) : null);
    return db.query("SELECT * FROM rooms WHERE room_id = ?").get(room_id);
  },

  listRooms() {
    return db.query(`SELECT r.*, (SELECT COUNT(*) FROM messages m WHERE m.room_id = r.room_id) AS message_count
      FROM rooms r ORDER BY r.created_at`).all();
  },

  postMessage(room_id: string, p: Record<string, any>) {
    const room = db.query("SELECT room_id FROM rooms WHERE room_id = ?").get(room_id) as any;
    if (!room) throw Object.assign(new Error("unknown room"), { status: 404 });
    const from_agent = String(p.from_agent || "").trim();
    const body = String(p.body || "");
    if (!from_agent) throw Object.assign(new Error("from_agent is required"), { status: 400 });
    if (!body) throw Object.assign(new Error("body is required"), { status: 400 });
    const agent = db.query("SELECT agent_id FROM agents WHERE agent_id = ?").get(from_agent) as any;
    if (!agent) throw Object.assign(new Error("unknown from_agent — join first"), { status: 404 });
    const ts = nowISO();
    const kind = p.kind ? String(p.kind).slice(0, 32) : "chat";
    const r = db.prepare("INSERT INTO messages (room_id, ts, from_agent, kind, body) VALUES (?,?,?,?,?)")
      .run(room_id, ts, from_agent, kind, body.slice(0, 20000));
    const msg = { seq: Number(r.lastInsertRowid), room_id, ts, from_agent, kind, body: body.slice(0, 20000) };
    broadcast(`room:${room_id}`, { type: "message", ...msg });
    return msg;
  },

  readMessages(room_id: string, since_seq = 0, limit = 100) {
    limit = Math.min(Math.max(1, limit), 500);
    return db.query(`SELECT seq, room_id, ts, from_agent, kind, body FROM messages
      WHERE room_id = ? AND seq > ? ORDER BY seq ASC LIMIT ?`).all(room_id, since_seq, limit);
  },
};

// --- websocket fan-out ----------------------------------------------------
type Sub = { topics: Set<string> };
const subs = new Set<any>();
function broadcast(topic: string, payload: any) {
  const data = JSON.stringify({ topic, ...payload });
  for (const ws of subs) {
    try {
      const s: Sub = ws.data.sub;
      if (s.topics.has(topic) || s.topics.has("*")) ws.send(data);
    } catch { /* drop dead sockets */ }
  }
}

// --- HTTP ------------------------------------------------------------------
const json = (data: any, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { "content-type": "application/json" } });
const err = (e: any) => json({ ok: false, error: String(e?.message || e) }, e?.status || 500);

let TOKEN = "";

function authorized(req: Request, url: URL): boolean {
  const h = req.headers.get("authorization");
  if (h === `Bearer ${TOKEN}`) return true;
  if (url.searchParams.get("token") === TOKEN && TOKEN) return true;
  return false;
}

async function handleFetch(req: Request, server: any): Promise<Response> {
  const url = new URL(req.url);
  const path = url.pathname;

  if (path === "/health") {
    const counts = {
      agents: (db.query("SELECT COUNT(*) AS c FROM agents").get() as { c: number }).c,
      rooms: (db.query("SELECT COUNT(*) AS c FROM rooms").get() as { c: number }).c,
      messages: (db.query("SELECT COUNT(*) AS c FROM messages").get() as { c: number }).c,
    };
    return json({ ok: true, service: "sovereign-chat", version: VERSION, uptime_s: Math.floor((Date.now() - BOOT_AT) / 1000), counts, ts: nowISO() });
  }

  // websocket stream
  if (path === "/v1/stream") {
    if (!authorized(req, url)) return json({ ok: false, error: "unauthorized" }, 401);
    const topics = new Set((url.searchParams.get("subscribe") || "room:fleet,presence").split(",").map((s) => s.trim()).filter(Boolean));
    const sub: Sub = { topics };
    const upgraded = server.upgrade(req, { data: { sub } });
    if (!upgraded) return json({ ok: false, error: "websocket upgrade failed" }, 500);
    return undefined as any; // handshake in flight — never return a Response here
  }

  // MCP over Streamable HTTP: JSON-RPC 2.0 single request/response, Bearer auth.
  // Lets tailnet/cell lanes use the chat MCP as a plain network API.
  if (path === "/v1/mcp" && req.method === "POST") {
    if (!authorized(req, url)) return json({ ok: false, error: "unauthorized" }, 401);
    const rpc = (await req.json().catch(() => null)) as any;
    const okR = (id: any, result: any) => json({ jsonrpc: "2.0", id, result });
    const failR = (id: any, code: number, message: string) => json({ jsonrpc: "2.0", id, error: { code, message } });
    if (!rpc || rpc.jsonrpc !== "2.0" || typeof rpc.method !== "string")
      return failR(rpc?.id ?? null, -32600, "invalid JSON-RPC 2.0 request");
    try {
      if (rpc.method === "initialize")
        return okR(rpc.id, { protocolVersion: "2024-11-05", capabilities: { tools: {} }, serverInfo: { name: "sovereign-chat", version: VERSION } });
      if (rpc.method === "notifications/initialized" || String(rpc.method).startsWith("notifications/"))
        return okR(rpc.id, {});
      if (rpc.method === "tools/list") return okR(rpc.id, { tools: MCP_TOOLS });
      if (rpc.method === "tools/call") {
        const { name, arguments: args } = rpc.params || {};
        const out = mcpCallTool(name, args || {});
        return okR(rpc.id, { content: [{ type: "text", text: JSON.stringify(out) }] });
      }
      if (rpc.method === "ping") return okR(rpc.id, {});
      return failR(rpc.id, -32601, "method not found: " + String(rpc.method));
    } catch (e: any) {
      return failR(rpc.id, -32000, String(e?.message || e));
    }
  }

  if (!path.startsWith("/v1/")) return json({ ok: false, error: "not found" }, 404);
  if (!authorized(req, url)) return json({ ok: false, error: "unauthorized" }, 401);

  try {
    const body = (req.method === "POST" || req.method === "PUT") ? await req.json().catch(() => ({})) : {};

    if (path === "/v1/join" && req.method === "POST") return json({ ok: true, ...store.join(body) });
    if (path === "/v1/presence" && req.method === "POST") return json(store.heartbeat(body));
    if (path === "/v1/presence" && req.method === "GET") return json({ ok: true, ...store.liveAgents() });
    if (path === "/v1/activity" && req.method === "GET") return json({ ok: true, ...store.activity() });
    if (path === "/v1/state" && req.method === "GET") return json({ ok: true, state: store.consolidatedState() });
    if (path === "/v1/rooms" && req.method === "GET") return json({ ok: true, rooms: store.listRooms() });
    if (path === "/v1/rooms" && req.method === "POST") return json({ ok: true, room: store.createRoom(body) });

    const m = path.match(/^\/v1\/rooms\/([^/]+)\/messages$/);
    if (m) {
      const room_id = decodeURIComponent(m[1]);
      if (req.method === "POST") return json({ ok: true, message: store.postMessage(room_id, body) });
      if (req.method === "GET") {
        const since = parseInt(url.searchParams.get("since_seq") || "0", 10) || 0;
        const limit = parseInt(url.searchParams.get("limit") || "100", 10) || 100;
        return json({ ok: true, room_id, messages: store.readMessages(room_id, since, limit) });
      }
    }
    return json({ ok: false, error: "not found" }, 404);
  } catch (e) {
    return err(e);
  }
}

const wsHandlers = {
  open(ws: any) { subs.add(ws); },
  close(ws: any) { subs.delete(ws); },
  message(ws: any, message: any) {
    // client topic management: {"subscribe": ["room:ops"]} / {"unsubscribe": [...]}
    try {
      const m = JSON.parse(String(message));
      const sub: Sub = ws.data.sub;
      if (Array.isArray(m.subscribe)) m.subscribe.forEach((t: string) => sub.topics.add(String(t)));
      if (Array.isArray(m.unsubscribe)) m.unsubscribe.forEach((t: string) => sub.topics.delete(String(t)));
      ws.send(JSON.stringify({ type: "subscribed", topics: [...sub.topics] }));
    } catch { /* ignore */ }
  },
};

// --- MCP (shared dispatch: stdio server + Streamable HTTP /v1/mcp) ---------------
const MCP_TOOLS = [
    { name: "join", description: "Join the fleet chat plane as an agent. summoner is required.", inputSchema: { type: "object", properties: { name: { type: "string" }, chat_id: { type: "string" }, agent_id: { type: "string" }, host_machine_id: { type: "string" }, hostname: { type: "string" }, hatchling_id: { type: "string" }, summoner: { type: "string" }, surface: { type: "string" }, activity: { type: "string" } }, required: ["name", "summoner"] } },
    { name: "heartbeat", description: "Presence heartbeat with current activity and counters.", inputSchema: { type: "object", properties: { agent_id: { type: "string" }, activity: { type: "string" }, counters: { type: "object" } }, required: ["agent_id"] } },
    { name: "post_message", description: "Post a message to a room.", inputSchema: { type: "object", properties: { room_id: { type: "string" }, from_agent: { type: "string" }, body: { type: "string" }, kind: { type: "string" } }, required: ["room_id", "from_agent", "body"] } },
    { name: "read_messages", description: "Replay room history.", inputSchema: { type: "object", properties: { room_id: { type: "string" }, since_seq: { type: "number" }, limit: { type: "number" } }, required: ["room_id"] } },
    { name: "list_presence", description: "Who is live right now.", inputSchema: { type: "object", properties: {} } },
    { name: "list_rooms", description: "List rooms.", inputSchema: { type: "object", properties: {} } },
    { name: "get_state", description: "Consolidated live picture: presence, activity, decision log, rooms. Read this instead of docs.", inputSchema: { type: "object", properties: {} } },
  ];

function mcpCallTool(name: string, args: Record<string, any>): any {
  if (name === "join") return store.join(args || {});
  if (name === "heartbeat") return store.heartbeat(args || {});
  if (name === "post_message") return store.postMessage(String(args?.room_id || "fleet"), args || {});
  if (name === "read_messages") return store.readMessages(String(args?.room_id || "fleet"), Number(args?.since_seq || 0), Number(args?.limit || 100));
  if (name === "list_presence") return store.liveAgents();
  if (name === "list_rooms") return store.listRooms();
  if (name === "get_state") return store.consolidatedState();
  throw new Error("unknown tool: " + String(name));
}

async function runMcp() {
  const token = (process.env.SOVEREIGN_CHAT_TOKEN || "").trim();
  if (token && token !== TOKEN) { console.error("MCP: bad SOVEREIGN_CHAT_TOKEN"); process.exit(1); }
  const rl = createInterface({ input: process.stdin, terminal: false });
  const respond = (id: any, result: any) =>
    process.stdout.write(JSON.stringify({ jsonrpc: "2.0", id, result }) + "\n");
  const respondErr = (id: any, code: number, message: string) =>
    process.stdout.write(JSON.stringify({ jsonrpc: "2.0", id, error: { code, message } }) + "\n");
  for await (const line of rl) {
    const t = line.trim();
    if (!t) continue;
    let msg: any;
    try { msg = JSON.parse(t); } catch { continue; }
    try {
      if (msg.method === "initialize") {
        respond(msg.id, { protocolVersion: "2024-11-05", capabilities: { tools: {} }, serverInfo: { name: "sovereign-chat", version: VERSION } });
      } else if (msg.method === "notifications/initialized" || msg.method?.startsWith("notifications/")) {
        // ack-only
      } else if (msg.method === "tools/list") {
        respond(msg.id, { tools: MCP_TOOLS });
      } else if (msg.method === "tools/call") {
        const { name, arguments: args } = msg.params || {};
        const out = mcpCallTool(name, args || {});
        respond(msg.id, { content: [{ type: "text", text: JSON.stringify(out) }] });
      } else if (msg.method === "ping") {
        respond(msg.id, {});
      } else {
        respondErr(msg.id, -32601, `method not found: ${msg.method}`);
      }
    } catch (e: any) {
      respondErr(msg.id, -32000, String(e?.message || e));
    }
  }
}

// --- boot ----------------------------------------------------------------------
TOKEN = await loadToken();

if (process.argv[2] === "mcp") {
  await runMcp();
  process.exit(0);
}

await seedFromLegacyJsonl();

const tsIP = await tailscaleIPv4();
const hosts = ["127.0.0.1", ...(tsIP ? [tsIP] : [])];
for (const hostname of hosts) {
  Bun.serve({ port: PORT, hostname, fetch: handleFetch, websocket: wsHandlers });
}
console.log(`[chat] sovereign-chat v${VERSION} listening on ${hosts.map((h) => `${h}:${PORT}`).join(" and ")} (state: ${STATE_DIR}/chat.db)`);
