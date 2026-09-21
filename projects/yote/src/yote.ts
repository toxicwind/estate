/**
 * Yote — Telegram gateway that uses OpenFang as an *external* HTTP service.
 * No OpenFang process env sharing; only OPENFANG_URL + optional OPENFANG_API_KEY.
 */
import { serve } from "bun";
import {
  mkdirSync,
  writeFileSync,
  existsSync,
  readFileSync,
  appendFileSync,
  renameSync,
} from "fs";
import { join, dirname, resolve } from "path";
import { fileURLToPath } from "url";
import { checkHealth, checkHealthLegacy } from "./lib/health";
import { Overlord } from "./lib/overlord";
import { handleMeshRequest } from "./lib/ghas-mesh-features";
import { OpenFangClient, RouteOption } from "./lib/openfang_api";
import { DeliveryLedger, BOT_CHANNEL } from "./lib/delivery-ledger";
import { sendValidated } from "./lib/validated-send";
import { resolveReplyText } from "./lib/resilient-route";

const __f = fileURLToPath(import.meta.url);
const __d = dirname(__f);
const PR = resolve(__d, "..");

/** Load KEY=VAL into process.env if unset (yote/.env is SSOT for telegram). */
function loadEnvFile(path: string) {
  if (!existsSync(path)) return;
  for (let line of readFileSync(path, "utf8").split("\n")) {
    line = line.trim();
    if (!line || line.startsWith("#")) continue;
    if (line.startsWith("export ")) line = line.slice(7);
    const eq = line.indexOf("=");
    if (eq < 1) continue;
    const k = line.slice(0, eq).trim();
    let v = line.slice(eq + 1).trim();
    if (
      (v.startsWith('"') && v.endsWith('"')) ||
      (v.startsWith("'") && v.endsWith("'"))
    ) {
      v = v.slice(1, -1);
    }
    if (k && process.env[k] === undefined) process.env[k] = v;
  }
}

loadEnvFile(join(PR, ".env"));
loadEnvFile(join(PR, "..", "config", "ports.env"));
loadEnvFile(join(process.env.HOME || "/home/toxic", ".secrets"));

const LD = join(PR, "logs");
const CD = join(PR, "config");
const CF = join(CD, "yote_chats.json");
const LF = join(CD, "last_update.json");
const LG = join(LD, "yote.log");
const PORT = Number(process.env.YOTE_PORT ?? "25102");
const TOK = process.env.YOTE_TELEGRAM_BOT_TOKEN ?? "";
const ALW = new Set(
  (process.env.YOTE_TELEGRAM_ALLOWED_USERS ?? "")
    .split(",")
    .map((s) => Number(s.trim()))
    .filter((n) => !isNaN(n) && n > 0),
);
const CHS = (process.env.YOTE_TELEGRAM_CHANNELS ?? "")
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean);
const LLM = process.env.LLM_PROXY_URL ?? "http://127.0.0.1:25100";
const OF_URL = process.env.OPENFANG_URL ?? "http://127.0.0.1:25103";
const DEFAULT_AGENT = (
  process.env.YOTE_OPENFANG_AGENT ||
  process.env.DEFAULT_MODEL?.replace(/^openfang:/, "") ||
  "coyote"
).replace(/^openfang:/, "");
const PUP_TRIX_ID = Number(process.env.YOTE_TARGET_USER || "716302190");

/** Audit 2026-09-17: auth-gate debug/quota endpoints. Set YOTE_API_KEY in yote/.env. */
const API_KEY = process.env.YOTE_API_KEY ?? "";
const WEBHOOK_SECRET = process.env.YOTE_WEBHOOK_SECRET ?? "";
const LOCKED = Boolean(API_KEY || WEBHOOK_SECRET);
function authorized(req: Request): boolean {
  const u = new URL(req.url);
  if (API_KEY) {
    const got =
      req.headers.get("x-yote-key") ?? u.searchParams.get("key") ?? "";
    if (got === API_KEY) return true;
  }
  if (WEBHOOK_SECRET) {
    const hs = req.headers.get("x-telegram-bot-api-secret-token") ?? "";
    if (hs === WEBHOOK_SECRET) return true;
  }
  return false;
}
function needAuth(req: Request): Response | null {
  if (!LOCKED) return null;
  if (authorized(req)) return null;
  return jres({ ok: false, error: "unauthorized" }, 401);
}

const ofClient = new OpenFangClient(OF_URL, process.env.OPENFANG_API_KEY || "", DEFAULT_AGENT);
const openfang = ofClient;

// WS3 delivery reliability: durable inbox, poll cursor, send-dedupe, DLQ.
// The ledger is the source of truth; last_update.json is only a mirror
// for external readers (kept for one release, then it can go).
const ledger = new DeliveryLedger();
const MAX_ATTEMPTS = Number(process.env.YOTE_MAX_ATTEMPTS || 5);
const DEAD_LETTER_DIR = `${process.env.HOME || "/home/toxic"}/.yote/dead-letter`;
let procUpdate: any = null; // the update currently being processed

/** Atomically persist the full failed update for the operator + sweeper. */
function writeDeadLetter(updateId: number, update: any, error: string) {
  try {
    mkdirSync(DEAD_LETTER_DIR, { recursive: true });
    const tmp = `${DEAD_LETTER_DIR}/${updateId}.json.tmp`;
    const fin = `${DEAD_LETTER_DIR}/${updateId}.json`;
    const doc = {
      update_id: updateId,
      channel_id: BOT_CHANNEL,
      received_at: new Date().toISOString(),
      chat_id: update?.message?.chat?.id ?? update?.callback_query?.message?.chat?.id ?? null,
      thread_id: update?.message?.message_thread_id ?? null,
      reply_to: update?.message?.message_id ?? null,
      reply_text: procUpdate?.lastReplyText ?? null,
      error,
      update,
    };
    writeFileSync(tmp, JSON.stringify(doc, null, 2));
    renameSync(tmp, fin);
    log(`dlq write ${fin}`);
  } catch (e: any) {
    log(`dlq write failed: ${e?.message ?? e}`);
  }
}

/** Re-drive crashed/pending inbox rows through proc (boot + poll loop). */
async function redrivePending(cooldownMs: number) {
  try {
    const rows = ledger.listRedrivable(BOT_CHANNEL, MAX_ATTEMPTS, Date.now(), cooldownMs);
    for (const row of rows) {
      let update: any;
      try {
        update = JSON.parse(row.update_json);
      } catch {
        ledger.markTerminal(BOT_CHANNEL, row.update_id, "dead_lettered", "update_json corrupt");
        writeDeadLetter(row.update_id, { raw: row.update_json }, "update_json corrupt");
        continue;
      }
      await proc(update);
    }
  } catch (e: any) {
    log(`redrive err ${e?.message ?? e}`);
  }
}

/** per-chat agent override (user can /agent coyote) */
const chatAgent: Record<string, string> = {};

let chats: Record<string, any> = {};
let last = 0;
let shut = false;
process.on("SIGTERM", () => { shut = true; });
process.on("SIGINT", () => { shut = true; });

const overlord = new Overlord({
  apiId: Number(process.env.YOTE_TELEGRAM_API_ID),
  apiHash: process.env.YOTE_TELEGRAM_API_HASH || "",
  session: process.env.YOTE_TELEGRAM_SESSION || "",
  onLog: (l) => log(l),
});
let overlordReady = false;
overlord
  .start()
  .then(() => {
    overlordReady = true;
    log("overlord connected");
  })
  .catch((e) => log(`overlord err: ${e.message ?? e}`));

function log(m: string) {
  const l = `[${new Date().toISOString()}] ${m}`;
  console.log(l);
  try {
    mkdirSync(dirname(LG), { recursive: true });
    appendFileSync(LG, l + "\n");
  } catch {
    /* */
  }
}
function loadChats() {
  try {
    if (existsSync(CF)) chats = JSON.parse(readFileSync(CF, "utf-8"));
  } catch {
    /* */
  }
}
function saveChats() {
  try {
    mkdirSync(dirname(CF), { recursive: true });
    writeFileSync(CF, JSON.stringify(chats, null, 2));
  } catch {
    /* */
  }
}
function loadLast() {
  try {
    if (existsSync(LF)) {
      const d = JSON.parse(readFileSync(LF, "utf-8"));
      last = d.lastUpdateId ?? 0;
    }
  } catch {
    /* */
  }
}
function saveLast() {
  try {
    const s = ledger.healthStats();
    mkdirSync(dirname(LF), { recursive: true });
    writeFileSync(
      LF,
      JSON.stringify(
        {
          lastUpdateId: s.pollOffset > 0 ? s.pollOffset - 1 : 0,
          pollCursor: s.pollOffset,
          processedWatermark: s.processedWatermark,
          updatedAt: new Date().toISOString(),
        },
        null,
        2,
      ),
    );
  } catch {
    /* */
  }
}
function cors(r: Response) {
  r.headers.set("Access-Control-Allow-Origin", "*");
  r.headers.set("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
  r.headers.set("Access-Control-Allow-Headers", "Content-Type,Authorization");
  return r;
}
function jres(d: any, s = 200) {
  return cors(
    new Response(JSON.stringify(d, null, 2), {
      status: s,
      headers: { "Content-Type": "application/json" },
    }),
  );
}

async function tg(m: string, b: any) {
  if (!TOK) return { ok: false, description: "no bot token" };
  try {
    const r = await fetch(`https://api.telegram.org/bot${TOK}/${m}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(b),
    });
    return await r.json();
  } catch {
    return { ok: false };
  }
}

/** WS3 validated send: shape-validated, response-checked, jitter-retried,
 *  dedupe-guarded. The update that is being processed lives in procUpdate
 *  so a failed reply can be dead-lettered with its full context. */
async function send(cid: number, t: string, o: any = {}) {
  const updateId = typeof o.updateId === "number" ? o.updateId : 0;
  if (procUpdate) procUpdate.lastReplyText = t;
  const res = await sendValidated(tg, ledger, cid, t, {
    updateId,
    threadId: o.threadId,
    replyTo: o.replyTo,
    parseMode: o.parse_mode,
  });
  if (!res.ok && res.permanent) {
    log(`send permanent fail update=${updateId}: ${res.error}`);
    throw new Error(`send failed permanently: ${res.error}`);
  }
  if (!res.ok) {
    log(`send transient fail update=${updateId} attempts=${res.attempts}: ${res.error}`);
    throw new Error(`send failed transiently: ${res.error}`);
  }
  if (res.deduped > 0) log(`send deduped update=${updateId} chunks=${res.deduped}`);
  return res;
}

/** OpenFang HTTP chat only — never llama-swap env wiring for OF agents */
async function ofChat(txt: string, agent?: string) {
  const a = agent || DEFAULT_AGENT;
  const r = await ofClient.chat(txt, { agent: a, max_tokens: 1024 });
  if (!r.ok) {
    return { ok: false as const, content: "", error: `HTTP ${r.status ?? "?"} ${r.error || "empty"}`, ms: r.ms ?? 0 };
  }
  return { ok: true as const, content: r.content, ms: r.ms ?? 0 };
}

/** WS3 resilient routing: OpenFang primary, direct-herd fallback on
 *  500-class/model-not-found/transport failure, actionable user error if
 *  both fail. Never returns a bare "openfang err" string anymore. */
async function hChat(cid: number, txt: string, o: any = {}) {
  const tb: any = { chat_id: cid, action: "typing" };
  if (o.threadId) tb.message_thread_id = o.threadId;
  await tg("sendChatAction", tb);
  const agent = chatAgent[String(cid)] || DEFAULT_AGENT;
  const updateId = typeof o.updateId === "number" ? o.updateId : 0;
  const routed = await resolveReplyText({
    ofChat: (t, a) => ofChat(t, a),
    herdUrl: LLM,
    herdModel: process.env.YOTE_HERD_FALLBACK_MODEL || "kimi-k3-nim",
    ofUrl: OF_URL,
    txt,
    agent,
    updateId,
    recordLatency: (ms) => ledger.recordOpenFangLatency(ms),
  });
  log(`route update=${updateId} via=${routed.route} of_ms=${routed.openfangMs}`);
  await send(cid, routed.text || "empty", o);
}

async function proc(up: any) {
  if (!up || typeof up !== "object") return;
  const updateId = up.update_id;
  if (typeof updateId !== "number" || !Number.isFinite(updateId)) return;
  // WS3: commit-before-process — the update is durable in the inbox AND
  // the poll cursor is advanced BEFORE any side effect. A crash after
  // this point re-drives the row; the send-dedupe claim guarantees the
  // user never sees a duplicate reply.
  const committed = ledger.commitInbound(BOT_CHANNEL, up);
  if (committed.status === "processed" || committed.status === "dead_lettered") {
    return; // already terminal: do not reprocess
  }
  ledger.saveOffset(BOT_CHANNEL, updateId + 1);
  last = Math.max(last, updateId + 1);
  saveLast();
  ledger.markAttempt(BOT_CHANNEL, updateId);
  const prevProcUpdate = procUpdate;
  procUpdate = { updateId, lastReplyText: null as string | null };
  try {
    await procInner(up, updateId);
    ledger.markTerminal(BOT_CHANNEL, updateId, "processed");
  } catch (e: any) {
    const attempts = ledger.markAttempt(BOT_CHANNEL, updateId);
    const errMsg = (e?.message ?? String(e)).slice(0, 300);
    if (attempts >= MAX_ATTEMPTS) {
      writeDeadLetter(updateId, up, errMsg);
      ledger.markTerminal(BOT_CHANNEL, updateId, "dead_lettered", errMsg);
      log(`dlq update=${updateId} attempts=${attempts}: ${errMsg}`);
    } else {
      log(`proc retry update=${updateId} attempts=${attempts}: ${errMsg}`);
    }
  } finally {
    procUpdate = prevProcUpdate;
  }
}

/** The original proc() body, now terminal-state aware. Every path that
 *  produces (or intentionally skips) a user-visible outcome ends with a
 *  markTerminal so the processed watermark can advance. */
async function procInner(up: any, updateId: number) {
  if (up.callback_query) {
    const cb = up.callback_query;
    log(`cb ${cb.from?.username}:${cb.data}`);
    await tg("answerCallbackQuery", { callback_query_id: cb.id });
    ledger.markTerminal(BOT_CHANNEL, updateId, "processed");
    return;
  }
  const msg = (up.message ?? up.edited_message) as any;
  if (!msg) {
    ledger.markTerminal(BOT_CHANNEL, updateId, "processed");
    return;
  }
  const cid = msg.chat?.id;
  const txt = (msg.text ?? "").trim();
  const uid = msg.from?.id;
  const tid = msg.message_thread_id;
  const mid = msg.message_id;
  if (!cid || !txt || !uid) {
    ledger.markTerminal(BOT_CHANNEL, updateId, "processed");
    return;
  }
  if (ALW.size > 0 && !ALW.has(uid)) {
    log(`unauth ${uid} in ${cid}`);
    await tg("sendMessage", {
      chat_id: cid,
      text: "unauth",
      message_thread_id: tid,
    });
    ledger.markTerminal(BOT_CHANNEL, updateId, "processed");
    return;
  }

  if (txt === "/start") {
    chats[String(cid)] = {
      user_id: uid,
      username: msg.from?.username,
      thread_id: tid,
      registered_at: new Date().toISOString(),
    };
    saveChats();
    await send(
      cid,
      `yote v0.6 · openfang external API @ ${OF_URL}\nagent: ${chatAgent[String(cid)] || DEFAULT_AGENT}\ncmds: /start /status /health /agent <name> /agents\nwatching: ${CHS.join(",") || "all"}\nallowed: ${Array.from(ALW).join(",")}`,
      { threadId: tid, updateId },
    );
    return;
  }

  if (txt === "/status") {
    const h = await checkHealthLegacy();
    const ofh = await ofClient.health();
    await send(
      cid,
      `status llama:${h.llama ? "ok" : "down"} openfang:${ofh.ok ? "ok" : "down"} (${ofh.ms}ms) agent:${chatAgent[String(cid)] || DEFAULT_AGENT} gpu:${h.gpu}`,
      { threadId: tid, updateId },
    );
    return;
  }

  if (txt === "/health") {
    const h = await checkHealth();
    const ofh = await ofClient.health();
    await send(
      cid,
      `health ${h.overall} dur:${h.durationMs}ms llama:${h.llamaSwap.healthy ? "ok" : "down"} of_api:${ofh.ok ? "ok" : "down"} of_body:${JSON.stringify(ofh.body).slice(0, 80)}`,
      { threadId: tid, updateId },
    );
    return;
  }

  if (txt === "/agents" || txt.startsWith("/agents ")) {
    const { ok, agents, error } = await ofClient.listAgents();
    if (!ok) {
      await send(cid, `agents err: ${error}`, { threadId: tid, updateId });
      return;
    }
    const lines = agents.map(
      (a) =>
        `• ${a.name} ${a.ready ? "ready" : a.state || "?"} [${a.model_provider || "?"}:${a.model_name || "?"}]`,
    );
    await send(
      cid,
      `openfang agents (${agents.length}) via ${OF_URL}/api/agents\n` +
        lines.join("\n"),
      { threadId: tid, updateId },
    );
    return;
  }

  if (txt.startsWith("/agent")) {
    const name = txt.replace(/^\/agent\s*/, "").trim();
    if (!name) {
      await send(
        cid,
        `current agent: ${chatAgent[String(cid)] || DEFAULT_AGENT}\nset: /agent coyote`,
        { threadId: tid, updateId },
      );
      return;
    }
    chatAgent[String(cid)] = name.replace(/^openfang:/, "");
    await send(cid, `agent set → ${chatAgent[String(cid)]}`, {
      threadId: tid,
    });
    return;
  }

  await hChat(cid, txt, { threadId: tid, replyTo: mid, updateId });
}

async function poll() {
  loadChats();
  // WS3: the sqlite cursor is the source of truth. On first boot after
  // the upgrade, adopt the legacy last_update.json as the cursor floor.
  last = ledger.loadOffset(BOT_CHANNEL);
  if (last <= 0) {
    loadLast();
    if (last > 0) {
      last = last + 1; // legacy stored lastUpdateId; cursor = next offset
      ledger.saveOffset(BOT_CHANNEL, last);
      saveLast();
    }
  }
  log(`poll start cursor=${last} token=${TOK ? "set" : "MISSING"}`);
  // WS3: boot reconciliation — replay updates left pending by a crash.
  await redrivePending(0);
  while (!shut) {
    try {
      const r: any = await tg("getUpdates", {
        offset: last,
        timeout: 25,
        allowed_updates: ["message", "edited_message", "callback_query"],
      });
      if (r.ok && Array.isArray(r.result)) {
        for (const u of r.result) await proc(u);
        last = ledger.loadOffset(BOT_CHANNEL);
      } else if (r.description) {
        log(`poll tg: ${r.description}`);
        await Bun.sleep(3000);
      }
    } catch (e: any) {
      log(`poll err ${e.message || e}`);
      await Bun.sleep(2000);
    }
    // WS3: periodic redrive of stuck rows (30s since-last-attempt cooldown).
    await redrivePending(30000);
    await Bun.sleep(500);
  }
}

async function testOverlordSend(target: string, text: string) {
  if (!overlordReady) return { ok: false, error: "overlord not connected" };
  const cl = overlord.client;
  const entity = await cl.getEntity(target);
  const sent = await cl.sendMessage(entity, { message: text });
  log(`overlord sent to ${target}: "${text}" msg_id=${sent.id}`);
  return { ok: true, sent: text, target, msgId: sent.id };
}

async function testE2E(chatId: number, text: string) {
  const prev = last;
  const fakeUp = {
    update_id: 999999999,
    message: {
      message_id: Date.now(),
      from: { id: chatId, username: "test" },
      chat: { id: chatId, type: "private" },
      date: Math.floor(Date.now() / 1000),
      text,
    },
  };
  await proc(fakeUp);
  last = prev;
  // e2e used the durable inbox path; reset the terminal test row so a
  // re-run is not skipped as already-processed.
  try {
    const { Database } = await import("bun:sqlite");
    const db = new Database(ledger.path);
    db.run("DELETE FROM telegram_inbox WHERE channel_id = ? AND update_id = 999999", [BOT_CHANNEL]);
    db.close();
  } catch {
    /* best effort */
  }
  saveLast();
  return {
    ok: true,
    sent: text,
    chatId,
    agent: chatAgent[String(chatId)] || DEFAULT_AGENT,
    via: "openfang-http",
  };
}

/** bedf89a9: pre-start port ownership guard.
 * The 2026-09-17 EADDRINUSE crash came from a duplicate yote binding 25102
 * while a live instance held it. Never crash blind on EADDRINUSE again:
 * probe-bind the port first; if occupied, identify the holder via its HTTP
 * identity and refuse to start a duplicate. Exit code 3 = "port refused"
 * (distinct from crash=1). serve() is also wrapped: if EADDRINUSE slips
 * through the probe race, the same refusal path fires. */
async function refuseDuplicate(port: number): Promise<never> {
  let owner = "unknown listener";
  try {
    const r = await fetch(`http://127.0.0.1:${port}/`, {
      signal: AbortSignal.timeout(3000),
    });
    if (r.ok) {
      const j = (await r.json().catch(() => null)) as any;
      owner =
        j && j.svc === "yote"
          ? `live yote instance (version=${j.version ?? "?"}, port=${j.port ?? "?"})`
          : `http responder (not yote)`;
    } else {
      owner = `http responder status=${r.status}`;
    }
  } catch {
    owner = "non-http listener";
  }
  log(
    `FATAL port-ownership: ${port} already held by ${owner} — refusing duplicate instance (bedf89a9 guard, exit 3)`
  );
  process.exit(3);
}

function portOccupied(port: number): boolean {
  try {
    const l = Bun.listen({
      hostname: "0.0.0.0",
      port,
      socket: { data() {} },
    });
    l.stop(true);
    return false;
  } catch {
    return true;
  }
}

if (portOccupied(PORT)) await refuseDuplicate(PORT);

let app: ReturnType<typeof serve>;
try {
  app = serve({

  port: PORT,
  async fetch(req) {
    const u = new URL(req.url);
    const p = u.pathname;
    if (p.startsWith("/mesh")) {
      const m = await handleMeshRequest(req, {
        service: "yote",
        version: "yote-0.6",
      });
      if (m) return cors(m);
    }
    if (p === "/health") {
      let s: any = null;
      try {
        s = ledger.healthStats();
      } catch {
        /* ledger unavailable: readiness is unaffected */
      }
      return cors(
        new Response(
          JSON.stringify({
            ok: true,
            telegram: s
              ? {
                  pollCursor: s.pollOffset,
                  processedWatermark: s.processedWatermark,
                  inboxPending: s.inboxPending,
                  inboxDeferred: s.inboxDeliveryUnknown,
                  dlqDepth: s.dlqDepth,
                  lastSuccessfulSend: s.lastSuccessfulSendMs
                    ? new Date(s.lastSuccessfulSendMs).toISOString()
                    : null,
                  lastOpenFangLatencyMs: s.lastOpenFangLatencyMs,
                }
              : null,
          }),
          { headers: { "Content-Type": "application/json" } },
        ),
      );
    }
    if (p === "/") {
      return jres({
        svc: "yote",
        version: "0.6",
        port: PORT,
        openfang_url: OF_URL,
        openfang_agent: DEFAULT_AGENT,
        integration: "openfang-http-api-only",
        llm_fallback_display: LLM,
        chs: CHS,
        overlord: overlordReady,
        bot_token_set: Boolean(TOK),
        pup_trix_id: PUP_TRIX_ID,
      });
    }

    // Proxy pure LLM path still available for debugging (not OpenFang)
    if (p === "/v1/chat/completions" && req.method === "POST") {
      const na0 = needAuth(req);
      if (na0) return na0;
      const b = await req.json().catch(() => ({}));
      // Prefer OpenFang OpenAI surface when model is openfang:*
      const model = String((b as any).model || "");
      if (model.startsWith("openfang:") || !model) {
        const messages = (b as any).messages || [];
        const lastUser =
          [...messages].reverse().find((m: any) => m.role === "user")
            ?.content || "";
        const agent = model.replace(/^openfang:/, "") || DEFAULT_AGENT;
        const r = await ofClient.chat(String(lastUser), {
          agent,
          max_tokens: (b as any).max_tokens,
        });
        return jres({
          id: `yote-of-${Date.now()}`,
          object: "chat.completion",
          model: r.model,
          choices: [
            {
              index: 0,
              message: { role: "assistant", content: r.content },
              finish_reason: "stop",
            },
          ],
          openfang: { ok: r.ok, error: r.error, ms: r.ms },
        });
      }
      const r = await fetch(`${LLM}/v1/chat/completions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(b),
      });
      const t = await r.text();
      return cors(
        new Response(t, {
          status: r.status,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }

    if (p === "/api/telegram/webhook" && req.method === "POST") {
      const na0 = needAuth(req);
      if (na0) return na0;
      const up = await req.json().catch(() => null);
      if (up) await proc(up);
      return jres({ ok: true });
    }

    // OpenFang external API diagnostics
    if (p === "/api/openfang/health") {
      return jres(await ofClient.health());
    }
    if (p === "/api/openfang/agents") {
      const na0 = needAuth(req);
      if (na0) return na0;
      return jres(await ofClient.listAgents());
    }
    if (p === "/api/openfang/models") {
      const na0 = needAuth(req);
      if (na0) return na0;
      return jres({ models: await ofClient.listOpenAiModels() });
    }
    if (p === "/api/openfang/probe" || p === "/api/openfang/probe-all") {
      const na0 = needAuth(req);
      if (na0) return na0;
      const report = await ofClient.probeAllAgents();
      return jres(report, report.fail ? 207 : 200);
    }
    if (p === "/api/openfang/chat" && req.method === "POST") {
      const na0 = needAuth(req);
      if (na0) return na0;
      const b: any = await req.json().catch(() => ({}));
      const r = await ofClient.chat(String(b.message || b.text || "hi"), {
        agent: b.agent,
        max_tokens: b.max_tokens,
      });
      return jres(r, r.ok ? 200 : 502);
    }
    if (p === "/api/openfang/chat") {
      const na0 = needAuth(req);
      if (na0) return na0;
      const msg = u.searchParams.get("msg") || "Reply with: YOTE_OF_OK";
      const agent = u.searchParams.get("agent") || DEFAULT_AGENT;
      const r = await ofClient.chat(msg, { agent, max_tokens: 64 });
      return jres(r, r.ok ? 200 : 502);
    }

    if (p === "/test/llm") {
      const na0 = needAuth(req);
      if (na0) return na0;
      const msg = u.searchParams.get("msg") || "say hi";
      const agent = u.searchParams.get("agent") || DEFAULT_AGENT;
      const r = await ofClient.chat(msg, { agent });
      return jres({
        ok: r.ok,
        agent: r.agent,
        model: r.model,
        response: r.content,
        error: r.error,
        ms: r.ms,
        fasterRouteAttempted: r.fasterRouteAttempted,
        fallbackUsed: r.fallbackUsed,
        via: "openfang-http",
      });
    }

    if (p === "/test/send" && req.method === "POST") {
      const na0 = needAuth(req);
      if (na0) return na0;
      const b: any = await req.json().catch(() => ({}));
      const cid = b.chat_id || PUP_TRIX_ID;
      const txt = b.text || "test from yote api (openfang-external)";
      const res = await tg("sendMessage", { chat_id: cid, text: txt });
      return jres({ ok: Boolean(res?.ok), sent: txt, chatId: cid, tg: res });
    }
    if (p === "/test/send") {
      const na0 = needAuth(req);
      if (na0) return na0;
      // GET: overlord MTProto send (optional) OR bot API to Pup Trix
      const mode = u.searchParams.get("mode") || "bot";
      const txt =
        u.searchParams.get("msg") ||
        `yote→openfang external test ${new Date().toISOString()}`;
      if (mode === "overlord") {
        const target = u.searchParams.get("to") || "crawlspace_coyote_bot";
        const r = await testOverlordSend(target, txt);
        return jres(r);
      }
      const cid = Number(u.searchParams.get("chat_id") || PUP_TRIX_ID);
      const res = await tg("sendMessage", { chat_id: cid, text: txt });
      return jres({
        ok: Boolean(res?.ok),
        mode: "bot",
        chatId: cid,
        sent: txt,
        tg: res,
        note: "Pup Trix target YOTE_TARGET_USER / 716302190",
      });
    }

    if (p === "/test/e2e" && req.method === "POST") {
      const na0 = needAuth(req);
      if (na0) return na0;
      const b: any = await req.json().catch(() => ({}));
      const cid = b.chat_id || PUP_TRIX_ID;
      const txt = b.text || "hello from yote e2e openfang";
      const r = await testE2E(cid, txt);
      return jres(r);
    }
    if (p === "/test/e2e") {
      const na0 = needAuth(req);
      if (na0) return na0;
      const cid = Number(u.searchParams.get("chat_id") || PUP_TRIX_ID);
      const txt = u.searchParams.get("msg") || "hello from yote e2e openfang";
      const r = await testE2E(cid, txt);
      return jres(r);
    }

    if (p === "/test/pup-trix") {
      const na0 = needAuth(req);
      if (na0) return na0;
      // Full path: OpenFang chat + bot message to real id
      const msg =
        u.searchParams.get("msg") ||
        "Pup Trix probe: reply with SOVEREIGN_YOTE_OK";
      const agent = u.searchParams.get("agent") || DEFAULT_AGENT;
      const of = await ofClient.chat(msg, { agent, max_tokens: 128 });
      const text = of.ok
        ? `🤖 openfang:${of.agent} (${of.ms}ms)\n${of.content}`
        : `openfang failed: ${of.error}`;
      const tgRes = await tg("sendMessage", {
        chat_id: PUP_TRIX_ID,
        text,
      });
      return jres({
        openfang: of,
        telegram: tgRes,
        chat_id: PUP_TRIX_ID,
        ok: of.ok && Boolean(tgRes?.ok),
      });
    }

    return cors(new Response("not found", { status: 404 }));
  },
});
} catch (e: any) {
  const msg = String(e?.message ?? e);
  if (/EADDRINUSE|address already in use/i.test(msg)) await refuseDuplicate(PORT);
  throw e;
}

log(
  `yote ${PORT} openfang=${OF_URL} agent=${DEFAULT_AGENT} bot=${TOK ? "set" : "MISSING"} overlord=${overlordReady} locked=${LOCKED}`,
);
if (TOK) poll().catch((e) => log(`poll fatal ${e}`));
else log("WARNING: YOTE_TELEGRAM_BOT_TOKEN missing — poll disabled");

export default app;
export { ofClient, openfang };
