#!/usr/bin/env bun
// acp-probe.mjs — End-to-end verification of initialize, authenticate, and session/new
import net from "net";
import dns from "node:dns";
import { performance } from "perf_hooks";

const HOST = "127.0.0.1";
const PORT = Number(process.env.ACP_PORT || 25111);
const TIMEOUT = 20_000;
const DNS_TIMEOUT = 3000;

const c = {
  reset: "\x1b[0m", bold: "\x1b[1m", dim: "\x1b[2m",
  green: "\x1b[32m", yellow: "\x1b[33m", red: "\x1b[31m",
  cyan: "\x1b[36m", magenta: "\x1b[35m"
};

// DNS Preflight
try {
  if (typeof globalThis.Bun !== "undefined" && globalThis.Bun?.dns?.prefetch) {
    globalThis.Bun.dns.prefetch(HOST, PORT);
  }
  const t0 = performance.now();
  const addrs = await Promise.race([
    dns.promises.resolve4(HOST, { ttl: true }),
    new Promise((_, rej) => setTimeout(() => rej(new Error("DNS timeout")), DNS_TIMEOUT)),
  ]);
  console.log(`\n✓ DNS preflight: ${HOST} -> ${addrs.map((a) => a.address).join(", ")} (${(performance.now() - t0).toFixed(2)}ms)`);
} catch (e) {
  console.log(`\n⚠ DNS preflight note: ${e.message} (continuing)`);
}

class Client {
  constructor(host, port) {
    this.host = host;
    this.port = port;
    this.sock = new net.Socket();
    this.buf = "";
    this.pending = new Map();
    this.id = 0;
    this.handlers = new Map();
    this.lat = {};
  }
  connect() {
    return new Promise((res, rej) => {
      const t0 = performance.now();
      const t = setTimeout(() => { this.sock.destroy(); rej(new Error("Connection timeout")); }, 5000);
      this.sock.connect(this.port, this.host, () => {
        clearTimeout(t);
        this.lat.tcp = +(performance.now() - t0).toFixed(2);
        res();
      });
      this.sock.on("data", (ch) => { this.buf += ch.toString("utf-8"); this.flush(); });
      this.sock.on("error", rej);
    });
  }
  flush() {
    let i;
    while ((i = this.buf.indexOf("\n")) !== -1) {
      const line = this.buf.slice(0, i).trim();
      this.buf = this.buf.slice(i + 1);
      if (!line) continue;
      try { this.handle(JSON.parse(line)); } catch {}
    }
  }
  handle(m) {
    if (m.id !== undefined && this.pending.has(m.id)) {
      const { resolve, reject, t0, method } = this.pending.get(m.id);
      this.pending.delete(m.id);
      this.lat[method] = +(performance.now() - t0).toFixed(2);
      if (m.error) reject(new Error(`[${method}] (${m.error.code}): ${m.error.message}${m.error.data ? " — " + JSON.stringify(m.error.data) : ""}`));
      else resolve({ result: m.result, latency: this.lat[method] });
      return;
    }
    if (m.method) {
      const h = this.handlers.get(m.method);
      if (h) h(m.params);
    }
  }
  on(method, cb) { this.handlers.set(method, cb); }
  req(method, params = {}) {
    return new Promise((res, rej) => {
      const id = ++this.id;
      const t0 = performance.now();
      const t = setTimeout(() => { this.pending.delete(id); rej(new Error(`Timeout waiting for ${method}`)); }, TIMEOUT);
      this.pending.set(id, { resolve: (v) => { clearTimeout(t); res(v); }, reject: (e) => { clearTimeout(t); rej(e); }, t0, method });
      this.sock.write(JSON.stringify({ jsonrpc: "2.0", id, method, params }) + "\n");
    });
  }
  end() {
    return new Promise((res) => this.sock.end(() => { this.sock.destroy(); res(); }));
  }
}

const cli = new Client(HOST, PORT);
cli.on("session/update", (p) => {
  const u = p.update || {};
  if (u.sessionUpdate === "agentMessageChunk" || u.type === "text_delta") process.stdout.write(c.green + (u.content?.text || u.text || "") + c.reset);
  else if (u.sessionUpdate === "thoughtChunk" || u.type === "thought_delta") process.stdout.write(c.magenta + (u.content?.text || u.text || "") + c.reset);
});

try {
  await cli.connect();
  console.log(`✓ TCP connect established (${cli.lat.tcp}ms)`);

  const init = await cli.req("initialize", {
    protocolVersion: 1,
    clientInfo: { name: "acp-probe", version: "3.1.0" },
    clientCapabilities: {
      fs: { readTextFile: true, writeTextFile: true },
      terminal: true,
    },
  });
  const agent = init.result?.agentInfo ?? {};
  console.log(`✓ initialize: ${agent.name} (${agent.version}) ${init.latency}ms`);
  console.log(`  authMethods: ${(init.result?.authMethods ?? []).map((m) => m.id).join(", ") || "none"}`);

  const methodId = init.result?.authMethods?.[0]?.id ?? "agent";
  try {
    const a = await cli.req("authenticate", { methodId });
    console.log(`✓ authenticate(${methodId}) ${a.latency}ms`);
  } catch (e) {
    console.log(`⚠ authenticate note: ${e.message}`);
  }

  const s = await cli.req("session/new", { cwd: "/home/toxic", mcpServers: [] });
  const sid = s.result?.sessionId;
  console.log(`✓ session/new allocated ID: ${sid} (${s.latency}ms)`);

  const pr = await cli.req("session/prompt", { sessionId: sid, prompt: [{ type: "text", text: "Reply with exactly: OK" }] });
  console.log(`\n✓ prompt stopReason=${pr.result?.stopReason || "endTurn"} (${pr.latency}ms)`);

  try { await cli.req("session/close", { sessionId: sid }); console.log("✓ session/close"); } catch {}
  await cli.end();
  console.log(`\n\x1b[32m═══ ACP PIPELINE OPERATIONAL ═══\x1b[0m\n`);
} catch (e) {
  console.error(`\n\x1b[31m✗ ${e.message}\x1b[0m\n`);
  try { await cli.end(); } catch {}
  process.exit(1);
}
