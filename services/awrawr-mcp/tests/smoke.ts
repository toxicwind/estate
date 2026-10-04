#!/usr/bin/env bun
/**
 * tests/smoke.ts — stdio transport smoke test for awrawr-mcp.
 *
 * Spawns the server EXACTLY as gatehouse does:
 *   /usr/bin/bash -l -c '/home/toxic/.bun/bin/bun <abs>/src/index.ts --stdio'
 * Runs: initialize -> notifications/initialized -> tools/list -> tools/call
 * (read-only) -> unknown-tool error, in BOTH framed (Content-Length) and
 * lines (newline-delimited JSON) request modes. Responses are always framed
 * with a mandatory trailing LF (mcp-go reads with ReadString('\n')).
 *
 * Usage: bun tests/smoke.ts [framed|lines]   (default: lines)
 */

import { spawn } from "node:child_process";

const BUN = "/home/toxic/.bun/bin/bun";
const SERVER = "/home/toxic/estate/services/awrawr-mcp/src/index.ts";

async function runMode(mode: "framed" | "lines"): Promise<void> {
  const child = spawn("/usr/bin/bash", ["-l", "-c", `${BUN} ${SERVER} --stdio`], {
    stdio: ["pipe", "pipe", "pipe"],
  });
  let out = Buffer.alloc(0);
  const waiters: Array<() => void> = [];
  child.stdout.on("data", (d: Buffer) => {
    out = Buffer.concat([out, d]);
    waiters.splice(0).forEach((w) => w());
  });
  let stderr = "";
  child.stderr.on("data", (d: Buffer) => { stderr += d.toString(); });

  const send = (obj: Record<string, unknown>): void => {
    const json = JSON.stringify(obj);
    if (mode === "framed") {
      child.stdin.write(`Content-Length: ${Buffer.byteLength(json, "utf8")}\r\n\r\n${json}\n`);
    } else {
      child.stdin.write(json + "\n");
    }
  };

  const readOne = async (timeoutMs = 15000): Promise<any> => {
    const start = Date.now();
    for (;;) {
      const idx = out.indexOf("Content-Length:");
      if (idx >= 0) {
        const hdrEnd = out.indexOf("\r\n\r\n", idx);
        if (hdrEnd >= 0) {
          const m = /content-length\s*:\s*(\d+)/i.exec(out.subarray(idx, hdrEnd).toString("latin1"));
          if (m) {
            const len = parseInt(m[1], 10);
            if (out.length >= hdrEnd + 4 + len) {
              const payload = out.subarray(hdrEnd + 4, hdrEnd + 4 + len).toString("utf8");
              out = out.subarray(hdrEnd + 4 + len);
              if (out.length === 0 || out[0] !== 10) {
                throw new Error("missing mandatory trailing LF after framed response");
              }
              out = out.subarray(1);
              return JSON.parse(payload);
            }
          }
        }
      }
      if (Date.now() - start > timeoutMs) {
        throw new Error(`timeout waiting for response (stderr tail: ${stderr.slice(-300)})`);
      }
      await new Promise<void>((r) => { waiters.push(r); setTimeout(r, 50); });
    }
  };

  const req = async (method: string, params: unknown, id: number | null): Promise<any> => {
    const msg: Record<string, unknown> = { jsonrpc: "2.0", method, params };
    if (id !== null) msg.id = id;
    send(msg);
    if (id === null) return null;
    return readOne();
  };

  // 1. initialize
  const init = await req("initialize",
    { protocolVersion: "2024-11-05", capabilities: {}, clientInfo: { name: "smoke", version: "1" } }, 1);
  if (!init?.result?.serverInfo?.name) throw new Error("bad initialize: " + JSON.stringify(init).slice(0, 200));
  console.log(`[${mode}] initialize ok: server=${init.result.serverInfo.name}`);

  // 2. notifications/initialized (no reply expected)
  await req("notifications/initialized", {}, null);

  // 3. tools/list — must be the full 39
  const list = await req("tools/list", {}, 2);
  const tools = list?.result?.tools ?? [];
  console.log(`[${mode}] tools/list: ${tools.length} tools`);
  if (tools.length !== 39) throw new Error(`expected 39 tools, got ${tools.length}`);

  // 4. read-only tool call
  const call = await req("tools/call", { name: "shim_info", arguments: {} }, 3);
  const text = call?.result?.content?.[0]?.text ?? "";
  console.log(`[${mode}] tools/call shim_info -> ${JSON.stringify(text).slice(0, 100)}`);
  if (!text) throw new Error("empty tool result");

  // 5. unknown tool -> -32601
  const bad = await req("tools/call", { name: "nope_nothing", arguments: {} }, 4);
  if (bad?.error?.code !== -32601) throw new Error("expected -32601 for unknown tool, got: " + JSON.stringify(bad).slice(0, 120));
  console.log(`[${mode}] unknown tool correctly -> -32601`);

  child.kill("SIGTERM");
  await new Promise((r) => child.on("exit", r));
  console.log(`[${mode}] SMOKE PASS`);
}

const arg = process.argv[2];
const mode = arg === "framed" ? "framed" : "lines";
await runMode(mode);
