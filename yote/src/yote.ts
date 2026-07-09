/**
 * src/yote.ts
 * Yote — Sovereign Telegram Bot + LLM Orchestrator
 * v0.4.1 — in-process GramJS Overlord, channels-filtered, with daemon
 */

import { serve } from "bun";
import { mkdirSync, writeFileSync, existsSync, readFileSync, appendFileSync } from "fs";
import { join, dirname, resolve } from "path";
import { fileURLToPath } from "url";

import { checkHealth } from "./lib/health";
import { listSovereignProcesses } from "./lib/process";
import { tailLog, listLogs } from "./lib/logs";
import { Overlord } from "./lib/overlord";
import { startDaemon } from "./lib/daemon";
import { YoteAgent } from "./lib/agent";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const PROJECT_ROOT = resolve(__dirname, "..");
const LOG_DIR = join(PROJECT_ROOT, "logs");
const CONFIG_DIR = join(PROJECT_ROOT, "config");
const REGISTERED_CHATS_FILE = join(CONFIG_DIR, "yote_chats.json");
const LOG_FILE = join(LOG_DIR, "yote.log");

// === Config ===
const YOTE_PORT = Number(process.env.YOTE_PORT || 25042);
const BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN || "";
const ALLOWED_IDS = new Set(
  (process.env.TELEGRAM_ALLOWED_USERS || "716302190")
   .split(",").map(s => Number(s.trim())).filter(n =>!isNaN(n))
);
const CHANNELS = (process.env.TELEGRAM_CHANNELS || "")
 .split(",").map(s => s.trim()).filter(Boolean); // -1004398809941,-1003747269638

const agent = new YoteAgent(); // now knows @puppertrix and your channels

let registeredChats: Record<string, any> = {};
let lastUpdateId = 0;

function log(msg: string) {
  const line = `[${new Date().toISOString()}] ${msg}`;
  console.log(line);
  try { mkdirSync(dirname(LOG_FILE), { recursive: true }); appendFileSync(LOG_FILE, line + "\n"); } catch {}
}

function loadChats() { try { if (existsSync(REGISTERED_CHATS_FILE)) registeredChats = JSON.parse(readFileSync(REGISTERED_CHATS_FILE, "utf-8")); } catch {} }
function saveChats() { try { mkdirSync(dirname(REGISTERED_CHATS_FILE), { recursive: true }); writeFileSync(REGISTERED_CHATS_FILE, JSON.stringify(registeredChats, null, 2)); } catch {} }

async function tgApi(method: string, body: any) {
  const res = await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/${method}`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body)
  });
  return res.json().catch(() => ({ ok: false }));
}

async function sendMsg(chatId: number, text: string, threadId?: number) {
  const MAX = 4000;
  const parts = text.length <= MAX? [text] : text.match(/[\s\S]{1,4000}/g) || [];
  for (const p of parts) {
    await tgApi("sendMessage", { chat_id: chatId, text: p, parse_mode: "Markdown", message_thread_id: threadId });
    await Bun.sleep(200);
  }
}

async function handleChat(chatId: number, text: string, threadId?: number) {
  await tgApi("sendChatAction", { chat_id: chatId, action: "typing", message_thread_id: threadId });
  try {
    const reply = await agent.chat(text);
    await sendMsg(chatId, reply || "⚠ Empty response", threadId);
  } catch (e) {
    await sendMsg(chatId, `⚠ LLM error: ${e}`, threadId);
  }
}

async function processUpdate(update: any) {
  const msg = update.message; if (!msg) return;
  lastUpdateId = update.update_id;
  const chatId = msg.chat?.id; const text = (msg.text || "").trim(); const userId = msg.from?.id;
  if (!chatId ||!text) return;
  if (ALLOWED_IDS.size &&!ALLOWED_IDS.has(userId)) return;

  if (text === "/start") {
    registeredChats[String(chatId)] = { user_id: userId, username: msg.from.username, registered_at: new Date().toISOString() };
    saveChats();
    await sendMsg(chatId, `🐺 *Yote v0.4.1 online*\n\nWatching: ${CHANNELS.join(", ") || "all"}`);
  } else if (text === "/status") {
    const h = await checkHealth(); await sendMsg(chatId, `Health: llama=${h.llama} openfang=${h.openfang}`);
  } else if (text.startsWith("/chat ")) {
    await handleChat(chatId, text.slice(6));
  } else {
    await handleChat(chatId, text);
  }
}

async function pollLoop() {
  while (true) {
    try {
      const params = new URLSearchParams({ timeout: "30", offset: String(lastUpdateId + 1) });
      const res = await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/getUpdates?${params}`, { signal: AbortSignal.timeout(35000) });
      const data: any = await res.json();
      for (const u of data.result || []) await processUpdate(u);
    } catch { await Bun.sleep(5000); }
  }
}

async function startUserbot() {
  const { TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_SESSION } = process.env;
  if (!TELEGRAM_API_ID ||!TELEGRAM_API_HASH ||!TELEGRAM_SESSION) {
    log("Overlord credentials missing — skipping");
    return null;
  }
  log(`Starting Overlord — filtering to ${CHANNELS.length} chats`);
  const overlord = new Overlord({
    apiId: Number(TELEGRAM_API_ID),
    apiHash: TELEGRAM_API_HASH,
    session: TELEGRAM_SESSION,
    channels: CHANNELS, // <-- THIS is the fix
    onNewMessage: async (m) => {
      log(`[Overlord] ${m.chatTitle}: ${m.sender}: ${m.text?.slice(0,80)}`);
      // optional: auto-reply in your channels
      if (CHANNELS.includes(m.chatId)) {
        const reply = await agent.chat(`[${m.sender} in ${m.chatTitle}]: ${m.text}`);
        // await overlord.sendMessage(m.chatId, reply); // uncomment to auto-reply
      }
    },
    onLog: log,
  });
  await overlord.start();
  return overlord;
}

function startHttp() {
  serve({
    port: YOTE_PORT,
    fetch: async (req) => {
      const url = new URL(req.url);
      if (url.pathname === "/health") return Response.json(await checkHealth());
      if (url.pathname === "/ps") return Response.json(await listSovereignProcesses());
      if (url.pathname === "/logs") return Response.json(listLogs());
      return new Response("yote v0.4.1");
    }
  });
  log(`HTTP :${YOTE_PORT}`);
}

async function main() {
  if (!BOT_TOKEN) throw new Error("TELEGRAM_BOT_TOKEN missing");
  log("=== YOTE v0.4.1 starting ===");
  loadChats();
  startHttp();
  const overlord = await startUserbot();
  startDaemon(overlord!); // <-- heartbeat, health, rotation
  await pollLoop();
}

main().catch(e => { log(`FATAL: ${e}`); process.exit(1); });