/**
 * src/yote.ts
 *
 * Yote — Sovereign Telegram Bot + LLM Orchestrator (core logic)
 *
 * This file is the merged heart of the project. It combines:
 *   - The full Telegram bot polling + command handling from the original yote.ts
 *   - Enhanced HTTP server (originally minimal /health) now also serves /ps, /logs/* via lib/*
 *   - Userbot (Overlord) subprocess management
 *   - OpenFang / local LLM chat bridge
 *   - Registration persistence, boot notifications, chunked messaging
 *
 * Path handling has been normalized for portability (no more hard-coded /home/toxic paths).
 * All supporting modules live in src/lib/.
 */

import { serve } from "bun";
import {
  mkdirSync,
  writeFileSync,
  existsSync,
  readFileSync,
  appendFileSync,
} from "fs";
import { join, dirname, resolve } from "path";
import { fileURLToPath } from "url";

// === Lib imports (merged modular pieces) ===
import { checkHealth } from "./lib/health";
import { listSovereignProcesses } from "./lib/process";
import { tailLog, listLogs } from "./lib/logs";

// === Project root resolution (portable) ===
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const PROJECT_ROOT = resolve(__dirname, "..");
const LOG_DIR = join(PROJECT_ROOT, "logs");
const CONFIG_DIR = join(PROJECT_ROOT, "config");
const REGISTERED_CHATS_FILE = join(CONFIG_DIR, "yote_chats.json");
const LOG_FILE = join(LOG_DIR, "yote.log");

// === Config from env (Bun auto-loads .env / .env.local) ===
const YOTE_PORT = parseInt(process.env.YOTE_PORT || "25042");
const BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN || "";
const ALLOWED_USERS = process.env.TELEGRAM_ALLOWED_USERS || "716302190";
const ALLOWED_IDS = new Set(
  ALLOWED_USERS.split(",")
    .map((u) => parseInt(u.trim()))
    .filter((id) => !isNaN(id)),
);

const OPENFANG_URL =
  process.env.OPENFANG_URL || "http://127.0.0.1:25004/v1/chat/completions";

const REGISTERED_CHATS_FILE_PATH = REGISTERED_CHATS_FILE; // for clarity

let registeredChats: Record<string, any> = {};
let lastUpdateId = 0;

function log(msg: string) {
  const ts = new Date().toISOString();
  const line = `[${ts}] ${msg}`;
  console.log(line);
  try {
    mkdirSync(dirname(LOG_FILE), { recursive: true });
    appendFileSync(LOG_FILE, line + "\n");
  } catch {}
}

function loadChats() {
  try {
    if (existsSync(REGISTERED_CHATS_FILE_PATH)) {
      registeredChats = JSON.parse(
        readFileSync(REGISTERED_CHATS_FILE_PATH, "utf-8"),
      );
      log(`Loaded ${Object.keys(registeredChats).length} registered chats`);
    }
  } catch (err) {
    log(`Failed to load chats: ${err}`);
  }
}

function saveChats() {
  try {
    mkdirSync(dirname(REGISTERED_CHATS_FILE_PATH), { recursive: true });
    writeFileSync(
      REGISTERED_CHATS_FILE_PATH,
      JSON.stringify(registeredChats, null, 2),
    );
  } catch (err) {
    log(`Failed to save chats: ${err}`);
  }
}

async function tgApi(method: string, body: any) {
  const url = `https://api.telegram.org/bot${BOT_TOKEN}/${method}`;
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return await res.json();
  } catch (err) {
    log(`TG API ${method} failed: ${err}`);
    return { ok: false };
  }
}

async function sendMsg(chatId: number, text: string, threadId?: number) {
  const MAX = 4000;
  const send = (txt: string) =>
    tgApi("sendMessage", {
      chat_id: chatId,
      text: txt,
      parse_mode: "Markdown",
      message_thread_id: threadId,
    });

  if (text.length <= MAX) {
    return send(text);
  }
  const chunks: string[] = [];
  let current = "";
  for (const line of text.split("\n")) {
    if (current.length + line.length + 1 > MAX) {
      chunks.push(current);
      current = line;
    } else {
      current += (current ? "\n" : "") + line;
    }
  }
  if (current) chunks.push(current);
  for (const chunk of chunks) {
    await send(chunk);
    await new Promise((r) => setTimeout(r, 300));
  }
}

async function handleStart(chatId: number, user: any, threadId?: number) {
  const userId = user.id || 0;
  const username = user.username || "unknown";
  const firstName = user.first_name || "";

  registeredChats[String(chatId)] = {
    user_id: userId,
    username,
    first_name: firstName,
    registered_at: new Date().toISOString(),
    ...(threadId !== undefined && { message_thread_id: threadId }),
  };
  saveChats();

  const health = await checkHealth();
  const statusLines = Object.entries(health).map(
    ([svc, ok]) => `  • ${svc}: ${ok ? "✅" : "❌"}`,
  );

  await sendMsg(
    chatId,
    `🐺 *Yote is online.*\n\n` +
      `Welcome, ${firstName}. You're registered.\n\n` +
      `*Stack Status:*\n` +
      statusLines.join("\n") +
      `\n\n*Commands:*\n` +
      `  /status — stack health + GPU\n` +
      `  /chat <message> — talk to the AI\n` +
      `  Any text → direct inference\n`,
    threadId,
  );
  log(`Registered chat ${chatId} for user ${username} (${userId})`);
}

async function handleStatus(chatId: number, threadId?: number) {
  const health = await checkHealth();
  const lines: string[] = ["🐺 *Yote — Stack Status*\n"];

  for (const [svc, ok] of Object.entries(health)) {
    lines.push(`  • ${svc}: ${ok ? "✅ UP" : "❌ DOWN"}`);
  }

  // GPU info via nvidia-smi (best effort)
  try {
    const proc = Bun.spawn([
      "nvidia-smi",
      "--query-gpu=memory.used,memory.total,temperature.gpu,utilization.gpu",
      "--format=csv,noheader,nounits",
    ]);
    const out = await new Response(proc.stdout).text();
    if (out.trim()) {
      const parts = out.split(",").map((p) => p.trim());
      lines.push(
        `\n*GPU:* ${parts[0]}/${parts[1]} MB | ${parts[2]}°C | ${parts[3]}% util`,
      );
    }
  } catch {}

  // Sovereign processes
  const procs = await listSovereignProcesses();
  if (procs.length > 0) {
    lines.push(`\n*Active Sovereign Processes:*`);
    for (const p of procs.slice(0, 8)) {
      lines.push(`  • ${p.pid} ${p.name}`);
    }
    if (procs.length > 8) lines.push(`  ... +${procs.length - 8} more`);
  }

  lines.push(`\n_Updated: ${new Date().toISOString()}_`);
  await sendMsg(chatId, lines.join("\n"), threadId);
}

async function handleChat(chatId: number, text: string, threadId?: number) {
  await tgApi("sendChatAction", {
    chat_id: chatId,
    action: "typing",
    message_thread_id: threadId,
  });
  try {
    const res = await fetch(OPENFANG_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: "openfang:coyote",
        messages: [{ role: "user", content: text }],
      }),
      signal: AbortSignal.timeout(120000),
    });
    if (res.ok) {
      const data: any = await res.json();
      const reply = data.choices?.[0]?.message?.content || "";
      await sendMsg(chatId, reply || "⚠️ Empty response from model.", threadId);
    } else {
      await sendMsg(
        chatId,
        `⚠️ HTTP error ${res.status} from OpenFang server.`,
        threadId,
      );
    }
  } catch (err) {
    log(`handleChat error: ${err}`);
    await sendMsg(chatId, `⚠️ Failed to fetch completions: ${err}`, threadId);
  }
}

async function processUpdate(update: any) {
  const updateId = update.update_id || 0;
  if (updateId > lastUpdateId) lastUpdateId = updateId;

  const msg = update.message;
  if (!msg) return;

  const chatId = msg.chat?.id;
  const threadId = msg.message_thread_id;
  const user = msg.from || {};
  const userId = user.id || 0;
  const text = (msg.text || "").trim();

  if (!chatId || !text) return;

  if (ALLOWED_IDS.size > 0 && !ALLOWED_IDS.has(userId)) {
    log(`Unauthorized user ${userId} (${user.username || "?"})`);
    await sendMsg(chatId, "🔒 Unauthorized.", threadId);
    return;
  }

  if (text === "/start") {
    await handleStart(chatId, user, threadId);
  } else if (text === "/status") {
    await handleStatus(chatId, threadId);
  } else if (text.startsWith("/chat ")) {
    await handleChat(chatId, text.substring(6).trim(), threadId);
  } else if (text.startsWith("/")) {
    await sendMsg(
      chatId,
      "Unknown command. Try /status or /chat <message>",
      threadId,
    );
  } else {
    await handleChat(chatId, text, threadId);
  }
}

async function sendBootNotification() {
  const health = await checkHealth();
  const lines = ["🟢 *Yote — Stack Boot Complete*\n"];
  for (const [svc, ok] of Object.entries(health)) {
    lines.push(`  • ${svc}: ${ok ? "✅" : "❌"}`);
  }
  lines.push(`\n_${new Date().toISOString()}_`);
  const msg = lines.join("\n");

  for (const [chatId, chatInfo] of Object.entries(registeredChats)) {
    const threadId = chatInfo.message_thread_id;
    await sendMsg(parseInt(chatId), msg, threadId);
    log(`Sent boot notification to chat ${chatId}`);
  }
}

async function pollLoop() {
  log("Starting Telegram Bot API long-poll loop");
  while (true) {
    try {
      const params = new URLSearchParams({
        timeout: "30",
        allowed_updates: JSON.stringify(["message"]),
        ...(lastUpdateId && { offset: String(lastUpdateId + 1) }),
      });
      const res = await fetch(
        `https://api.telegram.org/bot${BOT_TOKEN}/getUpdates?${params}`,
        {
          signal: AbortSignal.timeout(35000),
        },
      );
      if (res.ok) {
        const data: any = await res.json();
        for (const update of data.result || []) {
          try {
            await processUpdate(update);
          } catch (e) {
            log(`Error processing update: ${e}`);
          }
        }
      } else {
        log(`getUpdates HTTP ${res.status}`);
        await new Promise((r) => setTimeout(r, 5000));
      }
    } catch (err) {
      await new Promise((r) => setTimeout(r, 5000));
    }
  }
}

// === Overlord (Telethon userbot) subprocess starter ===
async function startUserbot() {
  const apiId = process.env.TELEGRAM_API_ID;
  const apiHash = process.env.TELEGRAM_API_HASH;
  if (!apiId || !apiHash) {
    log("Userbot credentials not set, skipping Overlord start.");
    return;
  }

  // Portable path resolution
  const overlordDir = join(PROJECT_ROOT, "scripts", "telethon");
  const venvPython = join(overlordDir, ".venv", "bin", "python3");
  const overlordScript = join(overlordDir, "overlord.py");

  const pythonCmd = existsSync(venvPython) ? venvPython : "python3";

  log("Starting userbot (Overlord) via Telethon subprocess...");
  try {
    const proc = Bun.spawn([pythonCmd, overlordScript], {
      cwd: overlordDir,
      env: process.env,
      stdout: "pipe",
      stderr: "pipe",
    });

    // stdout reader
    (async () => {
      const reader = proc.stdout.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";
        for (const line of lines) {
          if (line.trim()) {
            log(`[Overlord] ${line}`);
          }
        }
      }
    })();

    // stderr reader
    (async () => {
      const reader = proc.stderr.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";
        for (const line of lines) {
          if (line.trim()) {
            log(`[Overlord Error] ${line}`);
          }
        }
      }
    })();

    log("Userbot (Overlord) subprocess started.");
  } catch (err) {
    log(`Failed to start userbot subprocess: ${err}`);
  }
}

// === HTTP Server (enhanced with lib/* routes) ===
function startHttpServer() {
  serve({
    port: YOTE_PORT,
    async fetch(req) {
      const url = new URL(req.url);
      const pathname = url.pathname;

      if (pathname === "/health") {
        const health = await checkHealth();
        return Response.json({
          status: "ok",
          port: YOTE_PORT,
          app: "yote",
          version: "0.2.0",
          llm: health,
          timestamp: new Date().toISOString(),
        });
      }

      if (pathname === "/ps") {
        const procs = await listSovereignProcesses();
        return Response.json(procs);
      }

      if (pathname === "/logs") {
        return Response.json(listLogs());
      }

      if (pathname.startsWith("/logs/")) {
        const name = pathname.split("/")[2];
        const lines = await tailLog(name);
        return Response.json(lines);
      }

      return new Response(
        "🐺 yote — sovereign Telegram + LLM orchestrator\n" +
          "Endpoints: /health | /ps | /logs | /logs/:name",
        { status: 200 },
      );
    },
  });

  log(`[yote] HTTP server listening on :${YOTE_PORT}`);
}

// === Main entry ===
async function main() {
  if (!BOT_TOKEN) {
    log("TELEGRAM_BOT_TOKEN not set! Exiting.");
    process.exit(1);
  }

  log("==================================================");
  log("YOTE TELEGRAM SERVICE (BUN TS) — Starting (merged v0.2)");
  log(`Bot token: ...${BOT_TOKEN.substring(BOT_TOKEN.length - 8)}`);
  log(`Allowed users: ${Array.from(ALLOWED_IDS).join(", ")}`);
  log(`Project root: ${PROJECT_ROOT}`);
  log("==================================================");

  loadChats();
  startHttpServer();
  startUserbot();

  log("Waiting for stack health (llama + openfang)...");
  for (let i = 0; i < 30; i++) {
    const health = await checkHealth();
    if (health.llama && health.openfang) break;
    await new Promise((r) => setTimeout(r, 5000));
  }

  if (Object.keys(registeredChats).length > 0) {
    await sendBootNotification();
  }

  await pollLoop();
}

main().catch((err) => {
  log(`Fatal error in main: ${err}`);
  process.exit(1);
});
