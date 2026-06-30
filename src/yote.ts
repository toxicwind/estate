import { join, dirname } from "path";
import {
  mkdirSync,
  writeFileSync,
  existsSync,
  readFileSync,
  appendFileSync,
} from "fs";

// Load environment variables
const envPath = "/home/toxic/sovereign/.env.local";
if (existsSync(envPath)) {
  const envContent = readFileSync(envPath, "utf-8");
  for (const line of envContent.split("\n")) {
    const part = line.trim();
    if (part && !part.startsWith("#")) {
      const [key, ...valParts] = part.split("=");
      const val = valParts.join("=").replace(/^["']|["']$/g, "");
      process.env[key.trim()] = val;
    }
  }
}

const BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN || "";
const ALLOWED_USERS = process.env.TELEGRAM_ALLOWED_USERS || "13036673831";
const ALLOWED_IDS = new Set(
  ALLOWED_USERS.split(",")
    .map((u) => parseInt(u.trim()))
    .filter((id) => !isNaN(id)),
);

const NFCOT_URL = "http://127.0.0.1:25008/v1/chat/completions";
const LLAMA_HEALTH = "http://127.0.0.1:25001/health";
const NFCOT_HEALTH = "http://127.0.0.1:25008/v1/models";
const OPENFANG_HEALTH = "http://127.0.0.1:25004/api/health";
const REGISTERED_CHATS_FILE = "/home/toxic/sovereign/config/yote_chats.json";
const LOG_FILE = "/home/toxic/sovereign/logs/yote.log";

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
    if (existsSync(REGISTERED_CHATS_FILE)) {
      registeredChats = JSON.parse(
        readFileSync(REGISTERED_CHATS_FILE, "utf-8"),
      );
      log(`Loaded ${Object.keys(registeredChats).length} registered chats`);
    }
  } catch (err) {
    log(`Failed to load chats: ${err}`);
  }
}

function saveChats() {
  try {
    mkdirSync(dirname(REGISTERED_CHATS_FILE), { recursive: true });
    writeFileSync(
      REGISTERED_CHATS_FILE,
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

async function checkHealth(): Promise<Record<string, boolean>> {
  const services = {
    llama: LLAMA_HEALTH,
    nfcot: NFCOT_HEALTH,
    openfang: OPENFANG_HEALTH,
  };
  const results: Record<string, boolean> = {};
  for (const [name, url] of Object.entries(services)) {
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(3000) });
      results[name] = res.status === 200;
    } catch {
      results[name] = false;
    }
  }
  return results;
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
      `  /status — stack health\n` +
      `  /chat <message> — talk to the AI\n` +
      `  Any text → direct inference\n`,
    threadId,
  );
  log(`Registered chat ${chatId} for user ${username} (${userId})`);
}

async function handleStatus(chatId: number, threadId?: number) {
  const health = await checkHealth();
  const lines = ["🐺 *Yote — Stack Status*\n"];
  const portMap: Record<string, number> = {
    llama: 25001,
    nfcot: 25008,
    openfang: 25004,
  };
  for (const [svc, ok] of Object.entries(health)) {
    const port = portMap[svc] || "?";
    lines.append
      ? lines.push(`  • ${svc} (:${port}): ${ok ? "✅ UP" : "❌ DOWN"}`)
      : null;
  }
  // GPU info
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
    const res = await fetch(NFCOT_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: "qwen3.6-27b",
        messages: [
          {
            role: "system",
            content:
              "You are Yote, a sovereign AI assistant running on local hardware. Be concise and direct.",
          },
          { role: "user", content: text },
        ],
        max_tokens: 1024,
        temperature: 0.7,
      }),
      signal: AbortSignal.timeout(120000),
    });
    if (res.ok) {
      const data: any = await res.json();
      const reply = data.choices?.[0]?.message?.content || "";
      await sendMsg(chatId, reply || "⚠️ Empty response from model.", threadId);
    } else {
      await sendMsg(chatId, `⚠️ Inference error: HTTP ${res.status}`, threadId);
    }
  } catch (err) {
    await sendMsg(chatId, `⚠️ Error: ${err}`, threadId);
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
  const portMap: Record<string, number> = {
    llama: 25001,
    nfcot: 25008,
    openfang: 25004,
  };
  for (const [svc, ok] of Object.entries(health)) {
    const port = portMap[svc] || "?";
    lines.push(`  • ${svc} (:${port}): ${ok ? "✅" : "❌"}`);
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

async function startUserbot() {
  const apiId = process.env.TELEGRAM_API_ID;
  const apiHash = process.env.TELEGRAM_API_HASH;
  if (!apiId || !apiHash) {
    log("Userbot credentials not set, skipping userbot start.");
    return;
  }
  log("Starting userbot (Overlord)...");
  try {
    const { TelegramClient } = await import("telegram");
    const { StoreSession } = await import("telegram/sessions");
    const client = new TelegramClient(
      new StoreSession("overlord_session"),
      parseInt(apiId),
      apiHash,
      {
        connectionRetries: 5,
      },
    );
    await client.start({
      phoneNumber: async () => "",
      phoneCode: async () => "",
      onError: (err) => log(`Userbot error: ${err}`),
    });
    log("Userbot (Overlord) connected.");
  } catch (err) {
    log(`Failed to start userbot: ${err}`);
  }
}

async function main() {
  if (!BOT_TOKEN) {
    log("TELEGRAM_BOT_TOKEN not set!");
    process.exit(1);
  }

  log("==================================================");
  log("YOTE TELEGRAM SERVICE (BUN TS) — Starting");
  log(`Bot token: ...${BOT_TOKEN.substring(BOT_TOKEN.length - 8)}`);
  log(`Allowed users: ${Array.from(ALLOWED_IDS).join(", ")}`);
  log("==================================================");

  loadChats();
  startUserbot();

  log("Waiting for stack health...");
  for (let i = 0; i < 30; i++) {
    const health = await checkHealth();
    if (health.llama && health.nfcot && health.openfang) break;
    await new Promise((r) => setTimeout(r, 5000));
  }

  if (Object.keys(registeredChats).length > 0) {
    await sendBootNotification();
  }

  await pollLoop();
}

main();
