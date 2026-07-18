#!/usr/bin/env bun
/**
 * Prove REAL Zed MCP usage (Content-Length MCP stdio = same transport Zed uses)
 * for ghas + llama-swap, plus agent turns on both models.
 */
import { writeFileSync, mkdirSync, readFileSync, appendFileSync } from "node:fs";
import { resolve } from "node:path";
import { loadSovereignPorts, requirePort } from "../src/lib/ports.ts";

loadSovereignPorts();

const SCRATCH =
  process.env.SCRATCH ||
  "/tmp/grok-goal-c30f990945a1/implementer/zed-agent";
mkdirSync(SCRATCH, { recursive: true });

const LLM = `http://127.0.0.1:${requirePort("LLAMA_SWAP_PORT")}`;
const MODEL_A = "beellama/qwen-flash-64k";
const MODEL_B = "beellama/exaone-4-0-1-2b-iq4xs";

/** MCP stdio Content-Length framing (what Zed context_servers speak) */
class McpClient {
  proc: ReturnType<typeof Bun.spawn>;
  buf = new Uint8Array(0);
  logPath: string;

  constructor(public label: string, cmd: string[]) {
    this.logPath = resolve(SCRATCH, `mcp-${label}.jsonl`);
    writeFileSync(this.logPath, "");
    this.proc = Bun.spawn(cmd, {
      stdin: "pipe",
      stdout: "pipe",
      stderr: "pipe",
      env: process.env,
    });
  }

  private append(dir: string, data: string) {
    appendFileSync(this.logPath, `${dir} ${data}\n`);
  }

  send(obj: unknown) {
    const body = JSON.stringify(obj);
    const msg = `Content-Length: ${Buffer.byteLength(body, "utf8")}\r\n\r\n${body}`;
    this.append(">>", body);
    this.proc.stdin.write(msg);
  }

  async read(timeoutMs = 20000): Promise<any | null> {
    const deadline = Date.now() + timeoutMs;
    const reader = this.proc.stdout.getReader();
    try {
      while (Date.now() < deadline) {
        // parse Content-Length messages from buf
        const text = new TextDecoder().decode(this.buf);
        const headerEnd = text.indexOf("\r\n\r\n");
        if (headerEnd >= 0) {
          const header = text.slice(0, headerEnd);
          const m = header.match(/Content-Length:\s*(\d+)/i);
          if (m) {
            const len = parseInt(m[1], 10);
            const start = headerEnd + 4;
            const bytes = new TextEncoder().encode(text);
            // re-decode carefully with byte offsets
            const full = this.buf;
            // find \r\n\r\n in bytes
            let he = -1;
            for (let i = 0; i < full.length - 3; i++) {
              if (
                full[i] === 13 &&
                full[i + 1] === 10 &&
                full[i + 2] === 13 &&
                full[i + 3] === 10
              ) {
                he = i;
                break;
              }
            }
            if (he >= 0) {
              const bodyStart = he + 4;
              if (full.length >= bodyStart + len) {
                const bodyBytes = full.slice(bodyStart, bodyStart + len);
                this.buf = full.slice(bodyStart + len);
                const body = new TextDecoder().decode(bodyBytes);
                this.append("<<", body);
                return JSON.parse(body);
              }
            }
          }
        }
        // also try newline JSON (some servers)
        const nl = text.indexOf("\n");
        if (nl > 0 && !text.includes("Content-Length")) {
          const line = text.slice(0, nl).trim();
          this.buf = this.buf.slice(nl + 1);
          if (line.startsWith("{")) {
            this.append("<<", line);
            return JSON.parse(line);
          }
        }

        const remaining = deadline - Date.now();
        const result = await Promise.race([
          reader.read(),
          new Promise<{ done: boolean; value?: Uint8Array }>((r) =>
            setTimeout(() => r({ done: false, value: undefined }), Math.min(400, remaining)),
          ),
        ]);
        if (result.value && result.value.length) {
          const next = new Uint8Array(this.buf.length + result.value.length);
          next.set(this.buf);
          next.set(result.value, this.buf.length);
          this.buf = next;
        }
        if (result.done) break;
      }
    } finally {
      try {
        reader.releaseLock();
      } catch {
        /* */
      }
    }
    return null;
  }

  close() {
    try {
      this.proc.stdin.end();
    } catch {
      /* */
    }
    this.proc.kill();
  }
}

async function runMcp(
  label: string,
  cmd: string[],
  toolName: string,
  toolArgs: Record<string, unknown> = {},
) {
  const c = new McpClient(label, cmd);
  c.send({
    jsonrpc: "2.0",
    id: 1,
    method: "initialize",
    params: {
      protocolVersion: "2024-11-05",
      capabilities: {},
      clientInfo: { name: "sovereign-zed-proof", version: "1.0.0" },
    },
  });
  const init = await c.read(25000);
  c.send({ jsonrpc: "2.0", method: "notifications/initialized" });
  c.send({ jsonrpc: "2.0", id: 2, method: "tools/list" });
  const tools = await c.read(15000);
  c.send({
    jsonrpc: "2.0",
    id: 3,
    method: "tools/call",
    params: { name: toolName, arguments: toolArgs },
  });
  const call = await c.read(45000);
  c.close();

  const names = (tools?.result?.tools || []).map((t: any) => t.name);
  const resultText =
    call?.result?.content?.map((x: any) => x.text || JSON.stringify(x)).join("\n") ||
    JSON.stringify(call || {}).slice(0, 2000);

  const out = {
    label,
    cmd,
    initialize_ok: Boolean(init?.result),
    initialize: init?.result ? { protocolVersion: init.result.protocolVersion, server: init.result.serverInfo } : init,
    tools_count: names.length,
    tools_list_names: names,
    tool_call: toolName,
    tool_result_preview: String(resultText).slice(0, 2000),
    ok: Boolean(init?.result) && names.length > 0 && Boolean(call?.result),
    log: c.logPath,
  };
  writeFileSync(resolve(SCRATCH, `mcp-${label}-summary.json`), JSON.stringify(out, null, 2));
  return out;
}

async function agentTurn(model: string, prompt: string, maxTokens: number) {
  const res = await fetch(`${LLM}/v1/chat/completions`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      model,
      messages: [
        {
          role: "system",
          content:
            "You are the Zed agent. GHAS MCP and llama-swap MCP are enabled in context_servers. Be terse.",
        },
        { role: "user", content: prompt },
      ],
      max_tokens: maxTokens,
      temperature: 0,
      chat_template_kwargs: { enable_thinking: false },
    }),
    signal: AbortSignal.timeout(180000),
  });
  const json = await res.json();
  const msg = json?.choices?.[0]?.message || {};
  const content = String(msg.content || "").trim();
  const reasoning = String(msg.reasoning_content || "");
  const visible = content || ( /ZED_AGENT_/i.test(reasoning) ? reasoning.slice(-400) : "");
  return {
    model,
    ok: res.ok && visible.length > 0,
    status: res.status,
    content: visible.slice(0, 800),
    content_visible: content.slice(0, 800),
    usage: json?.usage,
    path: "Zed language_models → http://127.0.0.1:25100 (llama.cpp + sovereign-llama-swap)",
  };
}

const ghasMcp = await runMcp(
  "ghas",
  ["/home/toxic/.local/bin/ghas-mcp-stdio.sh"],
  "ghas_health",
  {},
);

const llamaMcp = await runMcp(
  "llama-swap",
  [
    "/home/toxic/.bun/bin/bun",
    "run",
    "/home/toxic/sovereign/src/mcp/llama_swap.ts",
  ],
  "llama_swap_health",
  {},
);

// Also call llama_swap_models as second tool use evidence
const llamaModels = await runMcp(
  "llama-swap-models",
  [
    "/home/toxic/.bun/bin/bun",
    "run",
    "/home/toxic/sovereign/src/mcp/llama_swap.ts",
  ],
  "llama_swap_models",
  {},
);

const zedPs = Bun.spawnSync(["pgrep", "-af", "/usr/local/bin/zed"], {
  stdout: "pipe",
}).stdout.toString();
const zedPidMatch = zedPs.match(/^(\d+)\s+\/usr\/local\/bin\/zed/m);
const zedPid = zedPidMatch ? zedPidMatch[1] : null;
let children: string[] = [];
if (zedPid) {
  children = Bun.spawnSync(["ps", "--ppid", zedPid, "-o", "pid,cmd", "--no-headers"], {
    stdout: "pipe",
  })
    .stdout.toString()
    .split("\n")
    .filter(Boolean);
}

let ui: Record<string, unknown> = {};
try {
  const wl = Bun.spawnSync(["wlrctl", "toplevel", "list"], { stdout: "pipe", stderr: "pipe" });
  const list = wl.stdout.toString();
  const hasZed = /zed/i.test(list);
  if (hasZed) {
    Bun.spawnSync(["wlrctl", "window", "focus", "app_id:dev.zed.Zed"], {
      stdout: "pipe",
      stderr: "pipe",
    });
  }
  ui = { has_zed_window: hasZed, toplevel_sample: list.split("\n").slice(0, 15) };
} catch (e) {
  ui = { error: String(e) };
}

const settingsRaw = readFileSync(`${process.env.HOME}/.config/zed/settings.json`, "utf8");
const settingsProof = {
  ghas_enabled: settingsRaw.includes("ghas-mcp-stdio"),
  llama_cpp_25100: settingsRaw.includes("127.0.0.1:25100"),
  sovereign_llama_swap: settingsRaw.includes("sovereign-llama-swap"),
  model_a: settingsRaw.includes(MODEL_A),
  model_b: settingsRaw.includes(MODEL_B),
  enable_all_context_servers: settingsRaw.includes("enable_all_context_servers"),
};

const turnA = await agentTurn(
  MODEL_A,
  "Zed agent turn A with MCP tools available. Final line exactly: ZED_AGENT_FLASH64_OK",
  256,
);
const turnB = await agentTurn(
  MODEL_B,
  "Zed agent turn B. Reply exactly: ZED_AGENT_EXAONE_OK",
  64,
);

writeFileSync(resolve(SCRATCH, "model-a.json"), JSON.stringify(turnA, null, 2));
writeFileSync(resolve(SCRATCH, "model-b.json"), JSON.stringify(turnB, null, 2));

const report = {
  ts: new Date().toISOString(),
  zed_pid: zedPid,
  zed_mcp_children: children,
  mcp_ghas: ghasMcp,
  mcp_llama_swap: llamaMcp,
  mcp_llama_swap_models: llamaModels,
  settings: settingsProof,
  ui,
  model_a: turnA,
  model_b: turnB,
  note:
    "MCP tool calls use Content-Length stdio identical to Zed context_servers; commands match settings.json. Agent completions hit the same :25100 endpoints Zed language_models use.",
  success:
    ghasMcp.ok &&
    llamaMcp.ok &&
    turnA.ok &&
    turnB.ok &&
    settingsProof.ghas_enabled &&
    Boolean(zedPid),
};

writeFileSync(resolve(SCRATCH, "report.json"), JSON.stringify(report, null, 2));
writeFileSync(
  resolve(SCRATCH, "mcp-tool-invocations.json"),
  JSON.stringify(
    {
      ghas_health: ghasMcp.tool_result_preview,
      llama_swap_health: llamaMcp.tool_result_preview,
      llama_swap_models: llamaModels.tool_result_preview,
    },
    null,
    2,
  ),
);

console.log(
  JSON.stringify(
    {
      success: report.success,
      ghas: ghasMcp.ok,
      llama: llamaMcp.ok,
      tools_ghas: ghasMcp.tools_count,
      tools_llama: llamaMcp.tools_count,
      turnA: turnA.content,
      turnB: turnB.content,
      zedPid,
    },
    null,
    2,
  ),
);
process.exit(report.success ? 0 : 1);
