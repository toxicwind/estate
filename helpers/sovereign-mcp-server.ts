#!/usr/bin/env bun
/**
 * sovereign-mcp-server.ts — First-class unified Bun MCP server.
 * Hardcore stdout logging (live, never file-only). stdio JSON-RPC 2.0.
 */
console.error(`[sovereign-mcp] STARTUP at ${new Date().toISOString()} pid=${process.pid}`);

import { join, resolve } from "node:path";
const SCRIPT_DIR = import.meta.dir;
const SOVEREIGN_ROOT = process.env.SOVEREIGN_ROOT || resolve(SCRIPT_DIR, "..");
const HELPERS_DIR = join(SOVEREIGN_ROOT, "helpers");

const TOOLS: Record<string, { desc: string; params: any[] }> = {
  estate_scan: { desc: "Fast estate path/broken-symlink audit (estate-scanner)", params: [{ name: "quick", type: "boolean" }] },
  estate_health_audit: { desc: "Probe 25xxx services concurrently (health-audit --json)", params: [] },
  estate_mesh_probe: { desc: "Mesh probe at :25127 (mesh-probe)", params: [] },
  estate_git_mutator: { desc: "Git mutator status / scan-secrets", params: [{ name: "subcmd", type: "string" }] },
  estate_safe_rg: { desc: "Token-budgeted regex/AST search (safe-rg-audit)", params: [{ name: "pattern", type: "string" }] },
  estate_paper_search: { desc: "arXiv / alphaXiv paper race (race_papers.py)", params: [{ name: "query", type: "string" }, { name: "maxn", type: "number" }] },
  estate_syntax_guard: { desc: "Pre-flight sub-millisecond AST/syntax check via ruff/oxlint/biome/tsc", params: [{ name: "file_path", type: "string" }] },
};

function log(msg: string) {
  const line = `[sovereign-mcp] ${new Date().toISOString()} ${msg}\n`;
  process.stderr.write(line);
}

const stdin = process.stdin;
stdin.setEncoding("utf8");
let buffer = "";

function send(resp: any) {
  const str = JSON.stringify(resp) + "\n";
  process.stdout.write(str);
  log(`RESPONSE id=${resp.id} method=${resp.result?.method || "resp"}`);
}

function handle(req: any) {
  log(`REQUEST id=${req.id} method=${req.method} params=${JSON.stringify(req.params ?? {})}`);
  try {
    if (req.method === "initialize") {
      send({ jsonrpc: "2.0", id: req.id, result: { protocolVersion: "2024-11-05", capabilities: { tools: { listChanged: true } }, serverInfo: { name: "sovereign-tools", version: "1.0.0" } } });
      return;
    }
    if (req.method === "notifications/initialized") return;
    if (req.method === "tools/list") {
      const list = Object.entries(TOOLS).map(([k, v]) => ({ name: k, description: v.desc, inputSchema: { type: "object", properties: Object.fromEntries((v.params || []).map(p => [p.name, { type: p.type || "string" }])) } }));
      send({ jsonrpc: "2.0", id: req.id, result: { tools: list } });
      return;
    }
    if (req.method === "tools/call") {
      const name = req.params?.name;
      const args = req.params?.arguments || {};
      log(`TOOL_CALL ${name} args=${JSON.stringify(args)}`);
      // Delegate to helper via Bun.spawn — live stdout only
      if (name === "estate_scan") {
        const proc = Bun.spawn(["bun", join(HELPERS_DIR, "estate-scanner.ts")], { stdout: "pipe", stderr: "pipe" });
        proc.output.then(o => {
          const out = new TextDecoder().decode(o.stdout) || new TextDecoder().decode(o.stderr) || "{}";
          send({ jsonrpc: "2.0", id: req.id, result: { content: [{ type: "text", text: out }] } });
        });
        return;
      }
      // For others, run the appropriate helper synchronously for simplicity
      try {
        let out = "{}";
        if (name === "estate_health_audit") {
          const res = Bun.spawnSync(["bun", join(HELPERS_DIR, "health-audit.ts"), "--json"]);
          out = new TextDecoder().decode(res.stdout) || "{}";
        } else if (name === "estate_mesh_probe") {
          const res = Bun.spawnSync(["bun", join(HELPERS_DIR, "mesh-probe.ts")]);
          out = new TextDecoder().decode(res.stdout) || res.stderr || "{}";
        } else if (name === "estate_git_mutator") {
          const cmd = args.subcmd || "status";
          const res = Bun.spawnSync(["bun", join(HELPERS_DIR, "git-mutator/cli.ts"), cmd], { cwd: SOVEREIGN_ROOT });
          out = new TextDecoder().decode(res.stdout) || "{}";
        } else if (name === "estate_safe_rg") {
          const pat = args.pattern || ".";
          const res = Bun.spawnSync(["bun", join(HELPERS_DIR, "safe-rg-audit.ts"), pat]);
          out = new TextDecoder().decode(res.stdout) || "{}";
        } else if (name === "estate_paper_search") {
          const q = args.query || "agent";
          const maxn = args.maxn || 5;
          const res = Bun.spawnSync(["python3", "/home/toxic/deep-paper-reader/paper-poller/bin/race_papers.py", q, "--maxn", String(maxn)]);
          out = new TextDecoder().decode(res.stdout) || "{}";
        } else if (name === "estate_syntax_guard") {
          const targetFile = args.file_path || join(HELPERS_DIR, "syntax-guard.ts");
          const res = Bun.spawnSync(["bun", join(HELPERS_DIR, "syntax-guard.ts"), targetFile]);
          out = new TextDecoder().decode(res.stdout) || new TextDecoder().decode(res.stderr) || "{}";
        }
        send({ jsonrpc: "2.0", id: req.id, result: { content: [{ type: "text", text: out }] } });
      } catch (e: any) {
        send({ jsonrpc: "2.0", id: req.id, error: { code: -32603, message: e.message } });
      }
      return;
    }
    send({ jsonrpc: "2.0", id: req.id, error: { code: -32601, message: "Method not found" } });
  } catch (e: any) {
    log(`ERROR ${e.message}`);
    send({ jsonrpc: "2.0", id: req.id, error: { code: -32603, message: e.message } });
  }
}

stdin.on("data", chunk => {
  buffer += chunk;
  let lines = buffer.split("\n");
  buffer = lines.pop() || "";
  for (const line of lines) {
    if (!line.trim()) continue;
    try {
      const req = JSON.parse(line);
      handle(req);
    } catch (e: any) {
      log(`PARSE_ERROR ${e.message} line=${line.slice(0, 200)}`);
    }
  }
});

stdin.on("end", () => {
  log("STDIN_END — shutting down live");
  process.exit(0);
});
