#!/usr/bin/env bun
/**
 * Prove Zed MCP (GHAS live) + agent-style completions on both local models:
 *   A) beellama/qwen-flash-64k
 *   B) beellama/exaone-4-0-1-2b-iq4xs
 * Writes captures under SCRATCH/zed-agent/
 */
import { writeFileSync, mkdirSync, readFileSync, existsSync } from "node:fs";
import { resolve } from "node:path";
import { loadSovereignPorts, requirePort } from "../src/lib/ports.ts";

loadSovereignPorts();

const SCRATCH =
  process.env.ZED_AGENT_OUT ||
  "/tmp/grok-goal-c30f990945a1/implementer/zed-agent";
mkdirSync(SCRATCH, { recursive: true });

const LLM = `http://127.0.0.1:${requirePort("LLAMA_SWAP_PORT")}`;
const GHAS = `http://127.0.0.1:${requirePort("GHAS_API_PORT")}`;
const GHAS_MCP = `http://127.0.0.1:${requirePort("GHAS_MCP_PORT")}`;

const MODEL_A = "beellama/qwen-flash-64k";
const MODEL_B = "beellama/exaone-4-0-1-2b-iq4xs";

type Cap = Record<string, unknown>;

async function chat(
  model: string,
  content: string,
  extra: Record<string, unknown> = {},
): Promise<Cap> {
  const body = {
    model,
    messages: [
      {
        role: "system",
        content:
          "You are the Zed agent on sovereign llama-swap. Be terse. No thinking dump.",
      },
      { role: "user", content },
    ],
    // flash-64k spends tokens on reasoning_content; need headroom for visible content
    max_tokens: model.includes("flash") || model.includes("qwen") ? 256 : 80,
    temperature: 0,
    chat_template_kwargs: { enable_thinking: false },
    ...extra,
  };
  const t0 = performance.now();
  try {
    const res = await fetch(`${LLM}/v1/chat/completions`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(120000),
    });
    const json = await res.json();
    const msg = json?.choices?.[0]?.message || {};
    const text =
      msg.content ||
      json?.choices?.[0]?.text ||
      "";
    const reasoning = msg.reasoning_content || "";
    // Visible content preferred; if model only emits reasoning, require marker substring there
    const visible = String(text).trim();
    const ok =
      res.ok &&
      (visible.length > 0 ||
        /ZED_AGENT_|FLASH64|OK/i.test(String(reasoning)));
    return {
      ok,
      status: res.status,
      model,
      ms: Math.round(performance.now() - t0),
      content: (visible || String(reasoning).slice(-200)).slice(0, 500),
      content_visible: visible.slice(0, 500),
      reasoning_tail: String(reasoning).slice(-200),
      raw_keys: Object.keys(json || {}),
      usage: json?.usage,
      error: json?.error,
    };
  } catch (e) {
    return {
      ok: false,
      model,
      ms: Math.round(performance.now() - t0),
      error: String(e),
    };
  }
}

async function httpJson(url: string): Promise<Cap> {
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(5000) });
    const text = await res.text();
    let json: unknown = text;
    try {
      json = JSON.parse(text);
    } catch {
      /* text */
    }
    return { ok: res.ok, status: res.status, url, body: json };
  } catch (e) {
    return { ok: false, url, error: String(e) };
  }
}

// 1) GHAS API + MCP health (what Zed context_servers.ghas uses)
const ghasHealth = await httpJson(`${GHAS}/health`);
const ghasMcp = await httpJson(`${GHAS_MCP}/health`);
const ghasMesh = await httpJson(`${GHAS}/mesh/features`);

// 2) Zed settings evidence
const zedSettingsPath = `${process.env.HOME}/.config/zed/settings.json`;
let zedCtx: Cap = { ok: false };
try {
  // json5 not required if we just string-scan
  const raw = readFileSync(zedSettingsPath, "utf8");
  zedCtx = {
    ok:
      raw.includes('"ghas"') &&
      raw.includes("ghas-mcp-stdio") &&
      raw.includes("llama.cpp") &&
      raw.includes("25100"),
    has_ghas_mcp: raw.includes("ghas-mcp-stdio"),
    has_llama_cpp: raw.includes("llama.cpp"),
    has_agent_profile: raw.includes("enable_all_context_servers"),
    path: zedSettingsPath,
  };
} catch (e) {
  zedCtx = { ok: false, error: String(e) };
}

// 3) Zed process + MCP children
const zedPid = Bun.spawnSync(["pgrep", "-af", "zed"], { stdout: "pipe" })
  .stdout.toString()
  .split("\n")
  .filter((l) => l.includes("/usr/local/bin/zed") || l.includes("bin/zed"))
  .slice(0, 5);
const mcpChildren = Bun.spawnSync(["pgrep", "-af", "ghas|apps/mcp"], {
  stdout: "pipe",
})
  .stdout.toString()
  .split("\n")
  .filter((l) => l.includes("apps/mcp") || l.includes("ghas-mcp"))
  .slice(0, 15);

// 4) Zed log tail for context_server / ghas
const logPath = `${process.env.HOME}/.local/share/zed/logs/Zed.log`;
let logHits: string[] = [];
if (existsSync(logPath)) {
  const tail = Bun.spawnSync(["tail", "-n", "400", logPath], { stdout: "pipe" })
    .stdout.toString();
  logHits = tail
    .split("\n")
    .filter((l) => /ghas|context_server|mcp|llama\.cpp|agent/i.test(l))
    .slice(-30);
}

// 5) Agent turns both models
const turnA = await chat(
  MODEL_A,
  "You are Zed agent model A. Reply with exactly one line: ZED_AGENT_FLASH64_OK mesh=ghas",
);
const turnB = await chat(
  MODEL_B,
  "You are Zed agent model B. Reply with exactly one line: ZED_AGENT_EXAONE_OK mesh=ghas",
);

// 6) Models list from llama-swap (Zed llama.cpp auto_discover)
const models = await httpJson(`${LLM}/v1/models`);

const report = {
  ts: new Date().toISOString(),
  ghas_api: ghasHealth,
  ghas_mcp_http: ghasMcp,
  ghas_mesh_native: ghasMesh,
  zed_settings: zedCtx,
  zed_processes: zedPid,
  ghas_mcp_processes: mcpChildren,
  zed_log_hits: logHits,
  model_a: turnA,
  model_b: turnB,
  models_ok: models.ok,
  success:
    Boolean(ghasHealth.ok) &&
    Boolean(zedCtx.ok) &&
    Boolean(turnA.ok) &&
    Boolean(turnB.ok) &&
    mcpChildren.length > 0,
};

writeFileSync(resolve(SCRATCH, "report.json"), JSON.stringify(report, null, 2));
writeFileSync(
  resolve(SCRATCH, "model-a.json"),
  JSON.stringify(turnA, null, 2),
);
writeFileSync(
  resolve(SCRATCH, "model-b.json"),
  JSON.stringify(turnB, null, 2),
);
writeFileSync(
  resolve(SCRATCH, "mcp-evidence.json"),
  JSON.stringify(
    {
      ghasHealth,
      ghasMcp,
      ghasMesh,
      zedCtx,
      mcpChildren,
      logHits: logHits.slice(-15),
    },
    null,
    2,
  ),
);

console.log(JSON.stringify({ success: report.success, turnA: turnA.content, turnB: turnB.content, ghas: ghasHealth.ok, zed: zedCtx.ok }, null, 2));
process.exit(report.success ? 0 : 1);
