import { spawn } from "child_process";
import { existsSync, readdirSync, readFileSync, statSync } from "fs";
import { join } from "path";

// fleet-bus-mcp v0.1.0 — first-class MCP for fleet-bus / squawk on the cell host.
// NOT Meta Hatch. Replaces gatehouse upstream "hatch-mcp" (name collision with
// /opt/hatch Jarvis cell daemon). Public agent door remains doorbell (:25202) →
// gatehouse; this server is the cell-side fleet-bus capability upstream.
//
// stdio MCP: newline-delimited JSON-RPC (mcpproxy-go ignores Content-Length-only).
// Mutating tools require confirm:true. Reports cell load1 for fan-out pressure.

const HATCH_BIN = process.env.HATCH_BIN || "/home/toxic/hatch/bin";
const HASHLINE_BIN = process.env.HASHLINE_BIN || "/home/toxic/.local/bin/hashline";
const SQUAWK_ROOT = process.env.SQUAWK_ROOT || "/home/toxic/.fleet-bus/squawk-root";
const MUSE_DB_SPOOL = process.env.MUSE_DB_SPOOL || "/home/toxic/.muse-db-shim";

function writeRpc(res: object) {
  // Newline-delimited JSON-RPC: one object per line. Content-Length
  // framing is NOT emitted — mcpproxy-go's stdio path silently
  // ignores Content-Length-only peers (zero tools discovered).
  process.stdout.write(JSON.stringify(res) + "\n");
}

function load1(): number {
  try {
    return parseFloat(readFileSync("/proc/loadavg", "utf8").split(" ")[0]);
  } catch {
    return -1;
  }
}

function run(cmd: string, args: string[], timeoutMs = 25000): Promise<{ ok: boolean; out: string; err: string; ms: number }> {
  const t0 = Date.now();
  return new Promise((resolve) => {
    const p = spawn(cmd, args, { stdio: ["ignore", "pipe", "pipe"] });
    let out = "", err = "";
    const timer = setTimeout(() => p.kill("SIGKILL"), timeoutMs);
    p.stdout.on("data", (d) => (out += d));
    p.stderr.on("data", (d) => (err += d));
    p.on("close", (code) => {
      clearTimeout(timer);
      resolve({ ok: code === 0, out, err, ms: Date.now() - t0 });
    });
    p.on("error", (e) => {
      clearTimeout(timer);
      resolve({ ok: false, out, err: String(e), ms: Date.now() - t0 });
    });
  });
}

function readChannel(channel: string, n = 10): { ok: boolean; messages: any[]; ms: number; error?: string } {
  const t0 = Date.now();
  const dir = join(SQUAWK_ROOT, channel);
  if (!existsSync(dir)) return { ok: false, messages: [], ms: Date.now() - t0, error: `no channel dir: ${dir}` };
  const files = readdirSync(dir).filter((f) => f.endsWith(".json")).sort();
  const tail = files.slice(-n);
  const messages = tail.map((f) => {
    try { return JSON.parse(readFileSync(join(dir, f), "utf8")); }
    catch { return { _file: f, _parse_error: true }; }
  });
  return { ok: true, messages, ms: Date.now() - t0 };
}

function listChannels(): string[] {
  if (!existsSync(SQUAWK_ROOT)) return [];
  return readdirSync(SQUAWK_ROOT).filter((d) => {
    try { return statSync(join(SQUAWK_ROOT, d)).isDirectory(); } catch { return false; }
  });
}

// ---- tool schemas ----

const TOOLS = [
  {
    name: "hatch_status",
    description: "Read-only. Hatch cell health: load1 vs 2 vCPUs, hatch-execd live/frozen descendant counts, open storm episode, yote load via bridge. HFT-aware: reports tool-path pressure so you know whether to fan out subagents now.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "hatch_load_audit",
    description: "Read-only. Full load-audit readout for the hatch cell + yote (the remote 16-core heavy tool host). Same data as ~/hatch/bin/load-audit, structured as JSON.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "squawk_list_channels",
    description: "Read-only. List squawk channels under the squawk-root (fleet, leads, ...).",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "squawk_read",
    description: "Read-only. Read the last N messages from a squawk channel (default fleet, n=10).",
    inputSchema: {
      type: "object",
      properties: {
        channel: { type: "string", description: "Channel name (default: fleet)" },
        n: { type: "number", description: "How many recent messages (default 10, max 100)" },
      },
    },
  },
  {
    name: "squawk_send",
    description: "DESTRUCTIVE-GATED. Publish a message to a squawk channel. Publish as the given from/sender (default ember). Requires confirm:true.",
    inputSchema: {
      type: "object",
      properties: {
        channel: { type: "string", description: "Channel name" },
        text: { type: "string", description: "Message body" },
        from: { type: "string", description: "Sender identity slug (default: ember). Lowercase one-word: remora, osprey, marten, ember, flicker, ..." },
        sender: { type: "string", description: "Alias for from" },
        confirm: { type: "boolean", description: "Must be true" },
      },
      required: ["channel", "text", "confirm"],
    },
  },
  {
    name: "muse_db_query",
    description: "Read-only. Submit a SELECT/WITH SQL query to the muse-db spool and wait for the drain worker. Only SELECT/WITH accepted (defense in depth).",
    inputSchema: {
      type: "object",
      properties: {
        sql: { type: "string", description: "SELECT or WITH ... SELECT statement" },
        timeout: { type: "number", description: "Seconds to wait for the drain worker (default 90)" },
      },
      required: ["sql"],
    },
  },
  {
    name: "hashline_read",
    description: "Read-only. Read a file with hashline xxh32 anchors (e.g. 42:a3) for stable patch targeting.",
    inputSchema: {
      type: "object",
      properties: { path: { type: "string", description: "Absolute file path" } },
      required: ["path"],
    },
  },
  {
    name: "hashline_patch",
    description: "DESTRUCTIVE-GATED. Apply a hashline patch to a file. Requires confirm:true. Patch format: [/path#HASH] then SWAP/INSERT/DELETE lines.",
    inputSchema: {
      type: "object",
      properties: {
        path: { type: "string", description: "Absolute file path" },
        patch: { type: "string", description: "hashline patch script" },
        confirm: { type: "boolean", description: "Must be true" },
      },
      required: ["path", "patch", "confirm"],
    },
  },
  {
    name: "fleet_status",
    description: "Read-only. List fleet-code sessions and their packet states (claimed paths, merged/quarantined/pending).",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "hatch_bin_list",
    description: "Read-only. List every canonical hatch-side binary in ~/hatch/bin with its size.",
    inputSchema: { type: "object", properties: {} },
  },
];

// ---- handlers ----

async function handleTool(name: string, args: any): Promise<any> {
  const t0 = Date.now();
  const L = load1();
  const pressure = L > 8 ? `OVER 4x (load1=${L.toFixed(1)}/2vCPU — do NOT fan out subagents now)` : `ok (load1=${L.toFixed(1)}/2vCPU)`;

  switch (name) {
    case "hatch_status": {
      const r = await run(join(HATCH_BIN, "load-audit"), []);
      return {
        content: [{ type: "text", text: r.ok ? r.out : (r.err || r.out) }],
        meta: { tool_ms: Date.now() - t0, cell_load: pressure },
      };
    }
    case "hatch_load_audit": {
      const r = await run(join(HATCH_BIN, "load-audit"), []);
      let structured: any = { raw: r.ok ? r.out : r.err };
      try {
        // load-audit prints human lines; parse the key numbers out.
        const lines = (r.ok ? r.out : r.err).split("\n");
        const cell = lines.find((l) => l.includes("hatch cell:"));
        const execd = lines.find((l) => l.includes("hatch-execd roots="));
        const storm = lines.find((l) => l.includes("storm episode:"));
        const yote = lines.find((l) => l.includes("yote (remote"));
        structured = { cell_line: cell, execd_line: execd, storm_line: storm, yote_line: yote, load1: L };
      } catch { /* keep raw */ }
      return {
        content: [{ type: "text", text: JSON.stringify(structured, null, 2) }],
        meta: { tool_ms: Date.now() - t0, cell_load: pressure },
      };
    }
    case "squawk_list_channels": {
      const chans = listChannels();
      return {
        content: [{ type: "text", text: JSON.stringify({ channels: chans }, null, 2) }],
        meta: { tool_ms: Date.now() - t0, cell_load: pressure },
      };
    }
    case "squawk_read": {
      const channel = String(args.channel || "fleet");
      const n = Math.min(Number(args.n || 10), 100);
      const res = readChannel(channel, n);
      return {
        content: [{ type: "text", text: JSON.stringify(res, null, 2) }],
        meta: { tool_ms: Date.now() - t0, cell_load: pressure },
      };
    }
    case "squawk_send": {
      if (args.confirm !== true) {
        return { content: [{ type: "text", text: "REFUSED: squawk_send is destructive-gated. Pass confirm:true to publish." }], isError: true };
      }
      const channel = String(args.channel || "");
      const text = String(args.text || "");
      if (!channel || !text) {
        return { content: [{ type: "text", text: "REFUSED: channel and text are required." }], isError: true };
      }
      // Optional from/sender; default ember for back-compat. Sanitize to one-word slug.
      const rawFrom = String(args.from ?? args.sender ?? "ember").toLowerCase().trim();
      if (!/^[a-z][a-z0-9_-]{0,31}$/.test(rawFrom)) {
        return { content: [{ type: "text", text: "REFUSED: from must match /^[a-z][a-z0-9_-]{0,31}$/ (lowercase one-word slug)." }], isError: true };
      }
      const from = rawFrom;
      // Hatch-side posts are unsigned (signing keys live on yote at 0600).
      // Drop a message file in the channel dir; the yote squawk-ws server
      // picks it up via inotify — same as `squawk send`.
      const dir = join(SQUAWK_ROOT, channel);
      const msg = { from, text, ts: Date.now() / 1000, via: "fleet-bus-mcp" };
      const fname = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}.json`;
      const { writeFileSync, mkdirSync } = await import("fs");
      mkdirSync(dir, { recursive: true });
      writeFileSync(join(dir, fname), JSON.stringify(msg, null, 2));
      process.stderr.write(`[fleet-bus-mcp] squawk_send confirmed: channel=${channel} from=${from} file=${fname}\n`);
      return {
        content: [{ type: "text", text: JSON.stringify({ sent: true, channel, from, file: fname }, null, 2) }],
        meta: { tool_ms: Date.now() - t0, cell_load: pressure },
      };
    }
    case "muse_db_query": {
      const sql = String(args.sql || "").trim();
      const up = sql.replace(/^[\s(]+/, "").toUpperCase();
      if (!up.startsWith("SELECT") && !up.startsWith("WITH")) {
        return { content: [{ type: "text", text: "REFUSED: only SELECT/WITH queries are accepted (read-only)." }], isError: true };
      }
      const timeout = Number(args.timeout || 90);
      const r = await run(join(HATCH_BIN, "muse-db"), [sql, "--timeout", String(timeout)], (timeout + 15) * 1000);
      return {
        content: [{ type: "text", text: r.ok ? r.out : (r.err || r.out) }],
        meta: { tool_ms: Date.now() - t0, cell_load: pressure },
      };
    }
    case "hashline_read": {
      const path = String(args.path || "");
      if (!path) return { content: [{ type: "text", text: "REFUSED: path required." }], isError: true };
      const r = await run(HASHLINE_BIN, ["read", path], 30000);
      return {
        content: [{ type: "text", text: r.ok ? r.out : (r.err || r.out) }],
        meta: { tool_ms: Date.now() - t0, cell_load: pressure },
      };
    }
    case "hashline_patch": {
      if (args.confirm !== true) {
        return { content: [{ type: "text", text: "REFUSED: hashline_patch is destructive-gated. Pass confirm:true to apply." }], isError: true };
      }
      const path = String(args.path || "");
      const patch = String(args.patch || "");
      if (!path || !patch) return { content: [{ type: "text", text: "REFUSED: path and patch are required." }], isError: true };
      // hashline patch reads the patch script on stdin.
      const t1 = Date.now();
      const res = await new Promise<{ ok: boolean; out: string; err: string }>((resolve) => {
        const p = spawn(HASHLINE_BIN, ["patch", path], { stdio: ["pipe", "pipe", "pipe"] });
        let out = "", err = "";
        p.stdout.on("data", (d) => (out += d));
        p.stderr.on("data", (d) => (err += d));
        p.stdin.write(patch);
        p.stdin.end();
        p.on("close", (code) => resolve({ ok: code === 0, out, err }));
        p.on("error", (e) => resolve({ ok: false, out, err: String(e) }));
      });
      process.stderr.write(`[fleet-bus-mcp] hashline_patch confirmed: path=${path} ms=${Date.now() - t1}\n`);
      return {
        content: [{ type: "text", text: res.ok ? res.out : (res.err || res.out) }],
        meta: { tool_ms: Date.now() - t0, cell_load: pressure },
      };
    }
    case "fleet_status": {
      // fleet-code status <session> per session; sessions live under ~/hatch/sessions or cwd sessions/.
      const { execSync } = await import("child_process");
      let sessions: string[] = [];
      for (const base of ["/home/toxic/hatch/sessions", join(process.cwd(), "sessions")]) {
        if (existsSync(base)) {
          sessions = sessions.concat(readdirSync(base).filter((d) => {
            try { return statSync(join(base, d)).isDirectory() && d !== ".archive"; } catch { return false; }
          }));
        }
      }
      const out: any = { sessions: [] };
      for (const s of sessions) {
        try {
          const txt = execSync(`${join(HATCH_BIN, "fleet-code")} status ${s}`, { encoding: "utf8", timeout: 15000 });
          out.sessions.push({ session: s, status: txt });
        } catch (e: any) {
          out.sessions.push({ session: s, error: String(e.message || e) });
        }
      }
      return {
        content: [{ type: "text", text: JSON.stringify(out, null, 2) }],
        meta: { tool_ms: Date.now() - t0, cell_load: pressure },
      };
    }
    case "hatch_bin_list": {
      const bins: any[] = [];
      if (existsSync(HATCH_BIN)) {
        for (const f of readdirSync(HATCH_BIN)) {
          try {
            const st = statSync(join(HATCH_BIN, f));
            if (st.isFile()) bins.push({ name: f, bytes: st.size });
          } catch { /* skip */ }
        }
      }
      return {
        content: [{ type: "text", text: JSON.stringify({ hatch_bin: HATCH_BIN, tools: bins }, null, 2) }],
        meta: { tool_ms: Date.now() - t0, cell_load: pressure },
      };
    }
    default:
      return { content: [{ type: "text", text: `unknown tool: ${name}` }], isError: true };
  }
}

// ---- JSON-RPC framing (crash-hardened) ----

process.on("uncaughtException", (e) => {
  process.stderr.write(`[fleet-bus-mcp] uncaughtException: ${e?.stack || e}\n`);
});
process.on("unhandledRejection", (e) => {
  process.stderr.write(`[fleet-bus-mcp] unhandledRejection: ${e}\n`);
});

let buf = Buffer.alloc(0);
function takeMessage(b: Buffer): { msg: any; rest: Buffer } | null {
  // Accept BOTH Content-Length headers and newline-delimited JSON.
  const s = b.toString("utf8");
  if (s.startsWith("Content-Length:")) {
    const m = /^Content-Length:\s*(\d+)\r?\n\r?/i.exec(s);
    if (!m) return null;
    const len = parseInt(m[1], 10);
    const headerEnd = m[0].length;
    if (b.length < headerEnd + len) return null;
    const body = b.subarray(headerEnd, headerEnd + len).toString("utf8");
    try {
      return { msg: JSON.parse(body), rest: b.subarray(headerEnd + len) };
    } catch (e: any) {
      process.stderr.write(`[fleet-bus-mcp] bad Content-Length body: ${e?.message || e}\n`);
      return { msg: null, rest: b.subarray(headerEnd + len) };
    }
  }
  const idx = s.indexOf("\n");
  if (idx === -1) {
    // No newline yet: if the whole buffer parses as one JSON object, take it.
    try { return { msg: JSON.parse(s), rest: Buffer.alloc(0) }; } catch { return null; }
  }
  const line = s.slice(0, idx);
  if (!line.trim()) return { msg: null, rest: b.subarray(idx + 1) };
  try {
    return { msg: JSON.parse(line), rest: b.subarray(idx + 1) };
  } catch (e: any) {
    process.stderr.write(`[fleet-bus-mcp] bad JSON line skipped: ${e?.message || e}\n`);
    return { msg: null, rest: b.subarray(idx + 1) };
  }
}

async function dispatch(msg: any) {
  // Notifications: no id, or method under notifications/ — never reply, never throw.
  const isNotification =
    msg.id === undefined || msg.id === null ||
    (typeof msg.method === "string" && msg.method.startsWith("notifications/"));
  if (typeof msg.method === "string" && msg.method.startsWith("notifications/")) {
    return; // ignore initialized, cancelled, etc.
  }
  if (msg.method === "initialize") {
    writeRpc({
      jsonrpc: "2.0", id: msg.id,
      result: {
        protocolVersion: "2024-11-05",
        capabilities: { tools: {}, resources: {}, prompts: {} },
        serverInfo: { name: "fleet-bus-mcp", version: "0.1.0" },
      },
    });
    return;
  }
  if (msg.method === "tools/list") {
    writeRpc({ jsonrpc: "2.0", id: msg.id, result: { tools: TOOLS } });
    return;
  }
  if (msg.method === "tools/call") {
    try {
      const result = await handleTool(msg.params?.name, msg.params?.arguments || {});
      writeRpc({ jsonrpc: "2.0", id: msg.id, result });
    } catch (e: any) {
      writeRpc({ jsonrpc: "2.0", id: msg.id, result: { content: [{ type: "text", text: String(e?.message || e) }], isError: true } });
    }
    return;
  }
  if (msg.method === "ping") {
    writeRpc({ jsonrpc: "2.0", id: msg.id, result: {} });
    return;
  }
  // Empty stubs so clients that probe these don't error-spam.
  if (msg.method === "resources/list") {
    writeRpc({ jsonrpc: "2.0", id: msg.id, result: { resources: [] } });
    return;
  }
  if (msg.method === "prompts/list") {
    writeRpc({ jsonrpc: "2.0", id: msg.id, result: { prompts: [] } });
    return;
  }
  if (isNotification) return;
  writeRpc({ jsonrpc: "2.0", id: msg.id, error: { code: -32601, message: `method not found: ${msg.method}` } });
}

process.stdin.on("data", async (chunk) => {
  try {
    buf = Buffer.concat([buf, chunk]);
    for (;;) {
      const taken = takeMessage(buf);
      if (!taken) break;
      buf = taken.rest;
      if (!taken.msg) continue;
      try {
        await dispatch(taken.msg);
      } catch (e: any) {
        process.stderr.write(`[fleet-bus-mcp] dispatch error: ${e?.stack || e}\n`);
      }
    }
  } catch (e: any) {
    process.stderr.write(`[fleet-bus-mcp] stdin loop error: ${e?.stack || e}\n`);
  }
});

process.stdin.on("error", (e) => {
  process.stderr.write(`[fleet-bus-mcp] stdin error: ${e}\n`);
});

process.stderr.write("[fleet-bus-mcp] v0.1.0 ready (newline JSON-RPC)\n");
