#!/usr/bin/env bun
/**
 * MCP: llama-swap / VS Code BYOK path tester (Bun).
 * Proves choices ≥ 1 on OpenAI-compat HTTP — same path oaicopilot hits.
 */
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { homedir } from "os";
import { join } from "path";
import { readFileSync, existsSync } from "fs";

const DEFAULT_BASE = (process.env.LLAMA_SWAP_BASE || "http://127.0.0.1:25100").replace(
  /\/$/,
  "",
);
const DEFAULT_MODEL = process.env.LLAMA_SWAP_MODEL || "beellama/qwen-flash-64k";
const SETTINGS =
  process.env.VSCODE_INSIDERS_SETTINGS ||
  join(homedir(), ".config/Code - Insiders/User/settings.json");
const CHAT_LM =
  process.env.VSCODE_INSIDERS_CHAT_LM ||
  join(homedir(), ".config/Code - Insiders/User/chatLanguageModels.json");

function readJsonFile(path: string): unknown {
  if (!existsSync(path)) throw new Error(`missing ${path}`);
  return JSON.parse(readFileSync(path, "utf8"));
}

function readTextFile(path: string): string {
  if (!existsSync(path)) throw new Error(`missing ${path}`);
  return readFileSync(path, "utf8");
}

async function httpJson(
  method: string,
  url: string,
  body?: unknown,
  timeoutMs = 60_000,
): Promise<{ code: number; parsed: unknown; raw: string }> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      method,
      headers: body
        ? { Accept: "application/json", "Content-Type": "application/json" }
        : { Accept: "application/json" },
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: ctrl.signal,
    });
    const raw = await res.text();
    let parsed: unknown = null;
    try {
      parsed = raw ? JSON.parse(raw) : null;
    } catch {
      parsed = null;
    }
    return { code: res.status, parsed, raw };
  } catch (e) {
    return { code: 0, parsed: null, raw: `request_failed: ${e}` };
  } finally {
    clearTimeout(t);
  }
}

function j(obj: unknown): string {
  return JSON.stringify(obj, null, 2);
}

export async function llamaSwapHealth(baseUrl = DEFAULT_BASE) {
  const base = baseUrl.replace(/\/$/, "");
  const { code, parsed, raw } = await httpJson("GET", `${base}/health`, undefined, 5000);
  return { http_status: code, body: parsed ?? raw.slice(0, 500) };
}

export async function llamaSwapModels(baseUrl = DEFAULT_BASE) {
  const base = baseUrl.replace(/\/$/, "");
  const { code, parsed, raw } = await httpJson("GET", `${base}/v1/models`, undefined, 10_000);
  if (!parsed || typeof parsed !== "object") {
    return { http_status: code, error: raw.slice(0, 800) };
  }
  const data = (parsed as { data?: Array<Record<string, unknown>> }).data || [];
  const models = data.map((m) => {
    let st: unknown = m.status;
    if (st && typeof st === "object" && st !== null && "value" in st) {
      st = (st as { value: unknown }).value;
    }
    return { id: m.id, status: st };
  });
  return { http_status: code, count: models.length, models };
}

export async function llamaSwapChat(opts: {
  prompt?: string;
  model?: string;
  base_url?: string;
  max_tokens?: number;
  stream?: boolean;
}) {
  const base = (opts.base_url || DEFAULT_BASE).replace(/\/$/, "");
  const model = opts.model || DEFAULT_MODEL;
  const body = {
    model,
    messages: [{ role: "user", content: opts.prompt ?? "Reply with exactly: OK" }],
    max_tokens: opts.max_tokens ?? 16,
    stream: opts.stream ?? false,
  };
  const { code, parsed, raw } = await httpJson(
    "POST",
    `${base}/v1/chat/completions`,
    body,
    120_000,
  );
  if (!parsed || typeof parsed !== "object") {
    return {
      http_status: code,
      ok: false,
      reason: "non_json_or_empty",
      raw_prefix: raw.slice(0, 600),
    };
  }
  const p = parsed as {
    choices?: Array<{ message?: { content?: string }; delta?: { content?: string } }>;
    model?: string;
    error?: unknown;
  };
  const choices = p.choices;
  const n = Array.isArray(choices) ? choices.length : 0;
  let content: string | undefined;
  if (n && choices![0]) {
    const msg = choices![0].message || choices![0].delta || {};
    content = msg.content;
  }
  return {
    http_status: code,
    ok: n >= 1 && code === 200,
    choices_count: n,
    model_requested: model,
    model_returned: p.model,
    content_preview: (content || "").slice(0, 200),
    error: p.error,
    vscode_symptom_if_fail:
      n >= 1 ? null : "Response contained no choices (empty choices[] or non-200)",
  };
}

export async function llamaSwapChatStream(opts: {
  prompt?: string;
  model?: string;
  base_url?: string;
  max_tokens?: number;
}) {
  const base = (opts.base_url || DEFAULT_BASE).replace(/\/$/, "");
  const body = {
    model: opts.model || DEFAULT_MODEL,
    messages: [{ role: "user", content: opts.prompt ?? "Say OK" }],
    max_tokens: opts.max_tokens ?? 8,
    stream: true,
  };
  try {
    const res = await fetch(`${base}/v1/chat/completions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(90_000),
    });
    const text = await res.text();
    let chunks = 0;
    const samples: string[] = [];
    for (const line of text.split("\n")) {
      const s = line.trim();
      if (!s.startsWith("data:")) continue;
      const payload = s.slice(5).trim();
      if (payload === "[DONE]") break;
      try {
        const obj = JSON.parse(payload);
        if (Array.isArray(obj.choices) && obj.choices.length) {
          chunks++;
          if (samples.length < 3) samples.push(payload.slice(0, 180));
        }
      } catch {
        /* skip */
      }
    }
    return { ok: chunks > 0, sse_chunks_with_choices: chunks, samples };
  } catch (e) {
    return { ok: false, error: String(e) };
  }
}

export function vscodeSettingsCheck() {
  const out: Record<string, unknown> = {
    settings_path: SETTINGS,
    chat_lm_path: CHAT_LM,
  };
  try {
    // fs.readFileSync — Bun.file().textSync() is unreliable on paths with spaces
    const s = readJsonFile(SETTINGS) as Record<string, unknown>;
    out["oaicopilot.baseUrl"] = s["oaicopilot.baseUrl"];
    out["chat.utilitySmallModel"] = s["chat.utilitySmallModel"];
    const models = s["oaicopilot.models"] || [];
    out["oaicopilot.models_count"] = Array.isArray(models) ? models.length : 0;
    out.baseUrl_is_25100 = String(s["oaicopilot.baseUrl"] || "").includes("25100");
    out.baseUrl_is_28080 = String(s["oaicopilot.baseUrl"] || "").includes("28080");
  } catch (e) {
    out.settings_missing = true;
    out.settings_error = String(e);
    out["oaicopilot.models_count"] = 0;
  }
  try {
    const t = readTextFile(CHAT_LM);
    out.chatLanguageModels_has_25100 = t.includes("25100");
    out.chatLanguageModels_has_28080 = t.includes("28080");
  } catch {
    out.chat_lm_missing = true;
    out.chatLanguageModels_has_25100 = false;
    out.chatLanguageModels_has_28080 = false;
  }
  const pluginOk = Boolean(
    out.baseUrl_is_25100 &&
      !out.baseUrl_is_28080 &&
      (Number(out["oaicopilot.models_count"]) || 0) >= 1,
  );
  const legacyOk = Boolean(
    out.chatLanguageModels_has_25100 && !out.chatLanguageModels_has_28080,
  );
  out.ok = pluginOk || legacyOk;
  out.path = pluginOk ? "oaicopilot_plugin" : legacyOk ? "customendpoint" : "none";
  return out;
}

export async function copilotByokE2e(opts: { model?: string; prompt?: string } = {}) {
  const settings = vscodeSettingsCheck();
  let base = String(settings["oaicopilot.baseUrl"] || DEFAULT_BASE).replace(/\/$/, "");
  let swapBase = base.endsWith("/v1") ? base.slice(0, -3) || base : base;
  if (!base.endsWith("/v1") && !base.includes("/v1")) {
    /* swap base is host */
  } else if (base.endsWith("/v1")) {
    swapBase = base.slice(0, -3);
  }

  const health = await llamaSwapHealth(swapBase);
  const models = await llamaSwapModels(swapBase);
  const ids = ((models as { models?: { id?: string }[] }).models || []).map((m) => m.id);
  let util = String(settings["chat.utilitySmallModel"] || "");
  if (util.startsWith("customendpoint/") || util.startsWith("oaicopilot/")) {
    util = util.split("/").slice(1).join("/");
  }
  const want = opts.model || util || DEFAULT_MODEL;
  const chat = await llamaSwapChat({
    prompt: opts.prompt ?? "Reply with exactly: OK",
    model: want,
    base_url: swapBase,
    max_tokens: 16,
  });
  const stream = await llamaSwapChatStream({
    prompt: "OK",
    model: want,
    base_url: swapBase,
    max_tokens: 8,
  });
  const ok = Boolean(
    settings.ok &&
      health.http_status === 200 &&
      ids.includes(want) &&
      (chat as { ok?: boolean }).ok &&
      (stream as { ok?: boolean }).ok,
  );
  return {
    ok,
    layer: "copilot_byok_http",
    not_tested: "vscode_ui_and_vscode.lm_api",
    oaicopilot_baseUrl: settings["oaicopilot.baseUrl"],
    utilitySmallModel: settings["chat.utilitySmallModel"],
    http_model_id: want,
    model_listed: ids.includes(want),
    health,
    chat,
    stream,
    if_fail_copilot_error: ok
      ? null
      : "Copilot would show: Response contained no choices (provideLanguageModelResponse)",
  };
}

/** CLI mode for mise run test-llm */
async function cliMain() {
  const cmd = process.argv[2] || "e2e";
  if (cmd === "health") console.log(j(await llamaSwapHealth()));
  else if (cmd === "models") console.log(j(await llamaSwapModels()));
  else if (cmd === "chat") console.log(j(await llamaSwapChat({})));
  else if (cmd === "stream") console.log(j(await llamaSwapChatStream({})));
  else if (cmd === "settings") console.log(j(vscodeSettingsCheck()));
  else if (cmd === "e2e") {
    const r = await copilotByokE2e();
    console.log(j(r));
    process.exit(r.ok ? 0 : 1);
  } else {
    console.error("usage: mcp_llama_swap.ts [e2e|health|models|chat|stream|settings|mcp]");
    process.exit(2);
  }
}

async function mcpMain() {
  const server = new McpServer({ name: "llama-swap-test", version: "1.0.0" });

  server.tool(
    "llama_swap_health",
    "GET {base}/health — llama-swap liveness.",
    { base_url: z.string().optional() },
    async ({ base_url }) => ({
      content: [{ type: "text", text: j(await llamaSwapHealth(base_url || DEFAULT_BASE)) }],
    }),
  );

  server.tool(
    "llama_swap_models",
    "GET {base}/v1/models — same catalog VS Code BYOK lists.",
    { base_url: z.string().optional() },
    async ({ base_url }) => ({
      content: [{ type: "text", text: j(await llamaSwapModels(base_url || DEFAULT_BASE)) }],
    }),
  );

  server.tool(
    "llama_swap_chat",
    "POST chat/completions — proves choices ≥ 1 (non-stream).",
    {
      prompt: z.string().optional(),
      model: z.string().optional(),
      base_url: z.string().optional(),
      max_tokens: z.number().optional(),
      stream: z.boolean().optional(),
    },
    async (args) => ({
      content: [{ type: "text", text: j(await llamaSwapChat(args)) }],
    }),
  );

  server.tool(
    "llama_swap_chat_stream",
    "POST streaming chat/completions; verify SSE chunks contain choices.",
    {
      prompt: z.string().optional(),
      model: z.string().optional(),
      base_url: z.string().optional(),
      max_tokens: z.number().optional(),
    },
    async (args) => ({
      content: [{ type: "text", text: j(await llamaSwapChatStream(args)) }],
    }),
  );

  server.tool(
    "vscode_settings_check",
    "Read Insiders settings: oaicopilot.baseUrl + models (plugin path).",
    {},
    async () => ({
      content: [{ type: "text", text: j(vscodeSettingsCheck()) }],
    }),
  );

  server.tool(
    "copilot_byok_e2e",
    "End-to-end BYOK path: settings + models + chat + stream.",
    {
      model: z.string().optional(),
      prompt: z.string().optional(),
    },
    async (args) => ({
      content: [{ type: "text", text: j(await copilotByokE2e(args)) }],
    }),
  );

  const transport = new StdioServerTransport();
  await server.connect(transport);
}

const mode = process.argv[2];
if (mode === "mcp" || !process.argv[2] && process.stdin.isTTY === false) {
  // default: if no args and not tty, run MCP; if explicit mcp, MCP
  if (mode === "mcp" || process.argv.length <= 2) {
    await mcpMain();
  } else {
    await cliMain();
  }
} else if (!mode) {
  await mcpMain();
} else {
  await cliMain();
}
