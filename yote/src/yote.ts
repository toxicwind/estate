/**
 * src/yote.ts
 * Yote — Sovereign Telegram Bot + LLM Orchestrator
 * v0.5.0 — production-hardened, Bun-native, llama-swap stack
 *
 * Stack: llama-swap (25021) → OpenFang (25004) → Yote (25042)
 */

import { serve } from "bun";
import {
  mkdirSync, writeFileSync, existsSync, readFileSync, appendFileSync,
} from "fs";
import { join, dirname, resolve } from "path";
import { fileURLToPath } from "url";

import {
  checkHealth,
  checkHealthLegacy,
  checkLlamaSwap,
  checkOpenFang,
  queryGpuStatus,
  fetchLlamaModels,
  fetchRunningModels,
  fetchLlamaMetrics,
  warmupModel,
  unloadModel,
  type HealthReport,
  type HealthStatus,
} from "./lib/health";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const PROJECT_ROOT = resolve(__dirname, "..");
const LOG_DIR = join(PROJECT_ROOT, "logs");
const CONFIG_DIR = join(PROJECT_ROOT, "config");
const REGISTERED_CHATS_FILE = join(CONFIG_DIR, "yote_chats.json");
const LAST_UPDATE_FILE = join(CONFIG_DIR, "last_update.json");
const LOG_FILE = join(LOG_DIR, "yote.log");

// === Config ===
const YOTE_PORT = Number(process.env.YOTE_PORT ?? "25042");
const BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN ?? "";
const ALLOWED_IDS = new Set(
  (process.env.TELEGRAM_ALLOWED_USERS ?? "")
    .split(",")
    .map((s) => Number(s.trim()))
    .filter((n) => !isNaN(n) && n > 0)
);
const CHANNELS = (process.env.TELEGRAM_CHANNELS ?? "")
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean);

let registeredChats: Record<string, { user_id: number; username?: string; thread_id?: number; registered_at: string }> = {};
let lastUpdateId = 0;
let server: ReturnType<typeof serve> | null = null;
let isShuttingDown = false;

// === Logging ===
function log(msg: string) {
  const line = `[${new Date().toISOString()}] ${msg}`;
  console.log(line);
  try {
    mkdirSync(dirname(LOG_FILE), { recursive: true });
    appendFileSync(LOG_FILE, line + "\n");
  } catch { /* ignore fs errors */ }
}

// === Persistence ===
function loadChats() {
  try {
    if (existsSync(REGISTERED_CHATS_FILE)) {
      registeredChats = JSON.parse(readFileSync(REGISTERED_CHATS_FILE, "utf-8"));
    }
  } catch { /* ignore parse errors */ }
}

function saveChats() {
  try {
    mkdirSync(dirname(REGISTERED_CHATS_FILE), { recursive: true });
    writeFileSync(REGISTERED_CHATS_FILE, JSON.stringify(registeredChats, null, 2));
  } catch { /* ignore fs errors */ }
}

function loadLastUpdate() {
  try {
    if (existsSync(LAST_UPDATE_FILE)) {
      const data = JSON.parse(readFileSync(LAST_UPDATE_FILE, "utf-8"));
      lastUpdateId = data.lastUpdateId ?? 0;
    }
  } catch { /* ignore parse errors */ }
}

function saveLastUpdate() {
  try {
    mkdirSync(dirname(LAST_UPDATE_FILE), { recursive: true });
    writeFileSync(LAST_UPDATE_FILE, JSON.stringify({ lastUpdateId, updatedAt: new Date().toISOString() }, null, 2));
  } catch { /* ignore fs errors */ }
}

// === CORS ===
function withCors(res: Response): Response {
  res.headers.set("Access-Control-Allow-Origin", "*");
  res.headers.set("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.headers.set("Access-Control-Allow-Headers", "Content-Type, Authorization");
  return res;
}

function jsonResponse(data: unknown, status = 200): Response {
  return withCors(new Response(JSON.stringify(data, null, 2), {
    status,
    headers: { "Content-Type": "application/json" },
  }));
}

// === Telegram Bot API ===
async function tgApi(method: string, body: Record<string, unknown>): Promise<{ ok: boolean; result?: unknown }> {
  try {
    const res = await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/${method}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return (await res.json()) as { ok: boolean; result?: unknown };
  } catch {
    return { ok: false };
  }
}

async function sendMsg(chatId: number, text: string, opts: { threadId?: number; replyTo?: number } = {}) {
  const MAX = 4000;
  const parts: string[] = [];
  let remaining = text;

  while (remaining.length > MAX) {
    let cut = remaining.lastIndexOf("\n", MAX);
    if (cut < MAX * 0.5) cut = remaining.lastIndexOf(" ", MAX);
    if (cut < 0) cut = MAX;
    parts.push(remaining.slice(0, cut));
    remaining = remaining.slice(cut).trimStart();
  }
  parts.push(remaining);

  for (const p of parts) {
    if (!p.trim()) continue;
    const body: Record<string, unknown> = {
      chat_id: chatId,
      text: p,
      parse_mode: "Markdown",
    };
    if (opts.threadId) body.message_thread_id = opts.threadId;
    if (opts.replyTo) body.reply_to_message_id = opts.replyTo;
    await tgApi("sendMessage", body);
    await Bun.sleep(200);
  }
}

// === LLM Agent (stub — replace with your YoteAgent) ===
const agent = {
  async chat(text: string): Promise<string> {
    // TODO: wire to your actual LLM backend via llama-swap
    // Example: POST to http://127.0.0.1:25021/v1/chat/completions
    return `Echo: ${text.slice(0, 200)}`;
  },
};

async function handleChat(chatId: number, text: string, opts: { threadId?: number; replyTo?: number } = {}) {
  const typingBody: Record<string, unknown> = { chat_id: chatId, action: "typing" };
  if (opts.threadId) typingBody.message_thread_id = opts.threadId;
  await tgApi("sendChatAction", typingBody);

  try {
    const reply = await agent.chat(text);
    await sendMsg(chatId, reply || "⚠️ Empty response", opts);
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    await sendMsg(chatId, `⚠️ LLM error: ${msg}`, opts);
  }
}

// === Update Processing ===
async function processUpdate(update: Record<string, unknown>) {
  if (!update || typeof update !== "object") return;

  lastUpdateId = update.update_id as number;
  saveLastUpdate();

  if (update.callback_query) {
    const cb = update.callback_query as Record<string, unknown>;
    log(`[callback] ${(cb.from as Record<string, unknown>)?.username}: ${cb.data}`);
    await tgApi("answerCallbackQuery", { callback_query_id: cb.id });
    return;
  }

  const msg = (update.message ?? update.edited_message) as Record<string, unknown> | undefined;
  if (!msg) return;

  const chatId = (msg.chat as Record<string, unknown>)?.id as number | undefined;
  const text = ((msg.text as string) ?? "").trim();
  const userId = (msg.from as Record<string, unknown>)?.id as number | undefined;
  const threadId = msg.message_thread_id as number | undefined;
  const messageId = msg.message_id as number | undefined;

  if (!chatId || !text || !userId) return;

  if (ALLOWED_IDS.size > 0 && !ALLOWED_IDS.has(userId)) {
    log(`Unauthorized user ${userId} in chat ${chatId}`);
    await tgApi("sendMessage", {
      chat_id: chatId,
      text: "🔒 Unauthorized.",
      message_thread_id: threadId,
    });
    return;
  }

  if (text === "/start") {
    registeredChats[String(chatId)] = {
      user_id: userId,
      username: (msg.from as Record<string, unknown>)?.username as string | undefined,
      thread_id: threadId,
      registered_at: new Date().toISOString(),
    };
    saveChats();
    await sendMsg(chatId, `🐺 *Yote v0.5.0 online*\n\nWatching: ${CHANNELS.join(", ") || "all"}\nAllowed: ${Array.from(ALLOWED_IDS).join(", ")}`, { threadId });
  } else if (text === "/status") {
    const h = await checkHealthLegacy();
    await sendMsg(chatId, `*Status*\n- *llama-swap*: ${h.llama ? "✅" : "❌"}\n- *openfang*: ${h.openfang ? "✅" : "❌"}\n- *gpu*: \`${h.gpu}\``, { threadId });
  } else if (text === "/health") {
    const h = await checkHealth();
    const lines = [
      `*Full Health Report*`,
      ``,
      `Overall: ${h.overall}`,
      `Duration: ${h.durationMs}ms`,
      ``,
      `*llama-swap*: ${h.llamaSwap.healthy ? "✅" : "❌"}`,
      `Models: ${h.llamaSwap.models.length}`,
      `Running: ${h.llamaSwap.running.length}`,
      ``,
      `*openfang*: ${h.openFang.healthy ? "✅" : "❌"}`,
      ``,
      `*gpu*: ${h.gpu.healthy ? "✅" : "❌"}`,
      `\`${h.gpu.summary}\``,
    ];
    if (h.warnings.length > 0) {
      lines.push("", `*Warnings:*`, ...h.warnings.map((w) => `• ${w}`));
    }
    await sendMsg(chatId, lines.join("\n"), { threadId });
  } else if (text === "/models") {
    const models = await fetchLlamaModels();
    const running = await fetchRunningModels();
    const lines = ["*Registered Models:*"];
    for (const m of models) {
      const isRunning = running.some((r) => r.id === m.id);
      lines.push(`• ${m.id}${isRunning ? " 🟢" : ""}`);
    }
    if (running.length > 0) {
      lines.push("", "*Running:*");
      for (const r of running) {
        lines.push(`• ${r.id} [${r.state}] port=${r.port ?? "null"}`);
      }
    }
    await sendMsg(chatId, lines.join("\n") || "No models registered.", { threadId });
  } else if (text.startsWith("/warmup ")) {
    const modelId = text.slice(8).trim();
    const result = await warmupModel(modelId);
    await sendMsg(chatId, result.success ? `🟢 Warming up *${modelId}*...` : `🔴 Warmup failed: ${result.error}`, { threadId });
  } else if (text.startsWith("/unload ")) {
    const modelId = text.slice(8).trim();
    const result = await unloadModel(modelId);
    await sendMsg(chatId, result.success ? `🟢 Unloaded *${modelId}*.` : `🔴 Unload failed: ${result.error}`, { threadId });
  } else if (text === "/unload") {
    const result = await unloadModel("all");
    await sendMsg(chatId, result.success ? "🟢 All models unloaded." : `🔴 Unload failed: ${result.error}`, { threadId });
  } else if (text.startsWith("/chat ")) {
    await handleChat(chatId, text.slice(6), { threadId, replyTo: messageId });
  } else if (text.startsWith("/")) {
    await sendMsg(chatId, "Commands: /start, /status, /health, /models, /warmup <model>, /unload [model], /chat <msg>", { threadId });
  } else {
    await handleChat(chatId, text, { threadId, replyTo: messageId });
  }
}

// === Polling Loop ===
let pollErrorCount = 0;
const MAX_POLL_BACKOFF = 30000;

async function pollLoop() {
  while (!isShuttingDown) {
    try {
      const params = new URLSearchParams({
        timeout: "30",
        offset: String(lastUpdateId + 1),
        limit: "100",
        allowed_updates: JSON.stringify(["message", "edited_message", "callback_query"]),
      });
      const res = await fetch(
        `https://api.telegram.org/bot${BOT_TOKEN}/getUpdates?${params}`,
        { signal: AbortSignal.timeout(35000) }
      );
      if (!res.ok) {
        const delay = Math.min(1000 * 2 ** pollErrorCount, MAX_POLL_BACKOFF);
        pollErrorCount++;
        log(`getUpdates HTTP ${res.status} — backing off ${delay}ms`);
        await Bun.sleep(delay);
        continue;
      }
      pollErrorCount = 0;
      const data = await res.json() as { result?: Array<Record<string, unknown>> };
      for (const u of data.result ?? []) {
        try {
          await processUpdate(u);
        } catch (e: unknown) {
          log(`processUpdate error: ${e instanceof Error ? e.message : String(e)}`);
        }
      }
    } catch (e: unknown) {
      if (isShuttingDown) break;
      const delay = Math.min(1000 * 2 ** pollErrorCount, MAX_POLL_BACKOFF);
      pollErrorCount++;
      log(`pollLoop error: ${e instanceof Error ? e.message : String(e)} — backing off ${delay}ms`);
      await Bun.sleep(delay);
    }
  }
  log("pollLoop exited cleanly");
}

// === HTTP Server ===
function startHttp() {
  server = serve({
    port: YOTE_PORT,
    idleTimeout: 0,
    fetch: async (req) => {
      const url = new URL(req.url);
      const path = url.pathname;

      if (req.method === "OPTIONS") {
        return withCors(new Response(null, { status: 204 }));
      }

      if (path === "/health") {
        return jsonResponse(await checkHealth());
      }
      if (path === "/status") {
        return jsonResponse(await checkHealthLegacy());
      }
      if (path === "/metrics") {
        const h = await checkHealthLegacy();
        const metrics = [
          `# HELP yote_health Health status (1=up, 0=down)`,
          `# TYPE yote_health gauge`,
          `yote_health{service="llama-swap"} ${h.llama ? 1 : 0}`,
          `yote_health{service="openfang"} ${h.openfang ? 1 : 0}`,
          `yote_health{service="gpu"} ${h.gpu.startsWith("Active") ? 1 : 0}`,
          `# HELP yote_uptime_seconds Process uptime`,
          `# TYPE yote_uptime_seconds counter`,
          `yote_uptime_seconds ${process.uptime()}`,
        ];
        return withCors(new Response(metrics.join("\n"), {
          headers: { "Content-Type": "text/plain; version=0.0.4" },
        }));
      }
      if (path === "/restart") {
        const auth = req.headers.get("Authorization");
        if (auth !== `Bearer ${process.env.YOTE_ADMIN_TOKEN}`) {
          return jsonResponse({ error: "Unauthorized" }, 401);
        }
        setTimeout(() => process.exit(0), 500);
        return jsonResponse({ status: "restarting" });
      }
      if (path === "/") {
        return jsonResponse({
          name: "yote",
          version: "0.5.0",
          uptime: process.uptime(),
          endpoints: ["/health", "/status", "/metrics", "/restart"],
        });
      }
      return jsonResponse({ error: "Not found" }, 404);
    },
  });
  log(`HTTP on :${YOTE_PORT}`);
}

async function stopHttp() {
  if (server) {
    try {
      await server.stop(true);
      log("HTTP stopped");
    } catch (e: unknown) {
      log(`HTTP stop error: ${e instanceof Error ? e.message : String(e)}`);
    }
    server = null;
  }
}

// === Graceful Shutdown ===
async function shutdown(signal: string) {
  if (isShuttingDown) return;
  isShuttingDown = true;
  log(`Signal ${signal} received. Shutting down...`);
  await stopHttp();
  log("Shutdown complete");
  process.exit(0);
}

// === Startup ===
function validateEnv(): string[] {
  const errors: string[] = [];
  if (!BOT_TOKEN) errors.push("TELEGRAM_BOT_TOKEN missing");
  if (ALLOWED_IDS.size === 0) errors.push("TELEGRAM_ALLOWED_USERS missing");
  return errors;
}

async function main() {
  const envErrors = validateEnv();
  if (envErrors.length > 0) {
    for (const e of envErrors) log(`ENV ERROR: ${e}`);
    throw new Error("Invalid environment");
  }

  log("=== YOTE v0.5.0 START ===");
  loadChats();
  loadLastUpdate();

  // Kill any existing process on YOTE_PORT
  try {
    const proc = Bun.spawn(["fuser", "-k", `${YOTE_PORT}/tcp`], { stdout: "pipe", stderr: "pipe" });
    await proc.exited;
    if (proc.exitCode === 0) {
      log(`Killed previous process on port ${YOTE_PORT}`);
      await Bun.sleep(1000);
    }
  } catch { /* ignore */ }

  startHttp();

  process.on("SIGTERM", () => shutdown("SIGTERM"));
  process.on("SIGINT", () => shutdown("SIGINT"));

  await pollLoop();
}

main().catch((e: unknown) => {
  log(`FATAL: ${e instanceof Error ? e.message : String(e)}`);
  process.exit(1);
});
