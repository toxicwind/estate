import { spawn } from "child_process";
import { readdirSync, statSync } from "fs";
import { join } from "path";

// Hardened tmux MCP server v2.0
// - Discovers ALL tmux sockets (default + named like tauhyperfix), not just the default
// - Read-only by default: tmux_list / tmux_capture need no confirmation
// - tmux_send is destructive-gated: requires explicit confirm:true in arguments

function writeRpc(res: object) {
  const s = JSON.stringify(res);
  process.stdout.write(
    `Content-Length: ${Buffer.byteLength(s, "utf8")}\r\n\r\n${s}`,
  );
}

function discoverSockets(): string[] {
  // Returns tmux -L socket names found under the tmux tmpdir.
  // Default socket is named "default"; named sockets (e.g. tauhyperfix) appear as files.
  const tmpdir = process.env.TMUX_TMPDIR || `/tmp/tmux-${process.getuid()}`;
  const found: string[] = [];
  try {
    for (const entry of readdirSync(tmpdir)) {
      const full = join(tmpdir, entry);
      try {
        const st = statSync(full);
        // tmux sockets are unix-domain sockets; also accept regular files
        // (some setups) but skip obvious non-sockets.
        if (st.isSocket() || st.isFile()) found.push(entry);
      } catch {
        /* race: ignore */
      }
    }
  } catch {
    /* no tmux dir: fall through to default */
  }
  if (!found.includes("default")) found.unshift("default");
  return found;
}

function runTmux(socket: string, args: string[]): Promise<string> {
  return new Promise((resolve) => {
    const fullArgs =
      socket && socket !== "default" ? ["-L", socket, ...args] : args;
    const p = spawn("tmux", fullArgs);
    let out = "";
    p.stdout.on("data", (d) => (out += d.toString()));
    p.stderr.on("data", (d) => (out += d.toString()));
    p.on("close", () => resolve(out.trim()));
  });
}

const TOOLS = [
  {
    name: "tmux_list",
    description:
      "List tmux sessions across ALL discovered sockets (default + named). Read-only.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "tmux_capture",
    description:
      "Capture pane scrollback (last 100 lines). Read-only. target like 'session:window.pane'. Optional socket name.",
    inputSchema: {
      type: "object",
      properties: {
        target: { type: "string" },
        socket: { type: "string" },
      },
      required: ["target"],
    },
  },
  {
    name: "tmux_send",
    description:
      "DESTRUCTIVE: send keys/command to a pane. Requires explicit confirm:true. Never send to interactive shells without the user's informed intent.",
    inputSchema: {
      type: "object",
      properties: {
        target: { type: "string" },
        command: { type: "string" },
        socket: { type: "string" },
        confirm: {
          type: "boolean",
          description: "Must be true to actually send. No default.",
        },
      },
      required: ["target", "command", "confirm"],
    },
  },
];

let buf = Buffer.alloc(0);
process.stdin.on("data", async (chunk) => {
  buf = Buffer.concat([buf, chunk]);
  while (true) {
    const idx = buf.indexOf("\r\n\r\n");
    if (idx === -1) break;
    const len = parseInt(
      (buf
        .subarray(0, idx)
        .toString()
        .match(/Content-Length:\s*(\d+)/i) || [])[1] || "0",
      10,
    );
    if (buf.length < idx + 4 + len) break;
    const msg = JSON.parse(buf.subarray(idx + 4, idx + 4 + len).toString());
    buf = buf.subarray(idx + 4 + len);

    if (msg.method === "initialize") {
      writeRpc({
        jsonrpc: "2.0",
        id: msg.id,
        result: {
          protocolVersion: "2024-11-05",
          capabilities: { tools: {} },
          serverInfo: { name: "tmux-mcp", version: "2.0" },
        },
      });
    } else if (msg.method === "notifications/initialized") {
      // no-op
    } else if (msg.method === "tools/list") {
      writeRpc({ jsonrpc: "2.0", id: msg.id, result: { tools: TOOLS } });
    } else if (msg.method === "tools/call") {
      const a = msg.params.arguments || {};
      const socket: string = a.socket || "default";
      try {
        if (msg.params.name === "tmux_list") {
          const parts: string[] = [];
          for (const s of discoverSockets()) {
            const out = await runTmux(s, ["list-sessions"]);
            parts.push(`[socket ${s}]\n${out || "(no sessions)"}`);
          }
          writeRpc({
            jsonrpc: "2.0",
            id: msg.id,
            result: { content: [{ type: "text", text: parts.join("\n") }] },
          });
        } else if (msg.params.name === "tmux_capture") {
          const out = await runTmux(socket, [
            "capture-pane",
            "-p",
            "-t",
            a.target,
            "-S",
            "-100",
          ]);
          writeRpc({
            jsonrpc: "2.0",
            id: msg.id,
            result: { content: [{ type: "text", text: out }] },
          });
        } else if (msg.params.name === "tmux_send") {
          if (a.confirm !== true) {
            writeRpc({
              jsonrpc: "2.0",
              id: msg.id,
              error: {
                code: -32602,
                message:
                  "Refused: tmux_send requires explicit confirm:true. This is a destructive action.",
              },
            });
          } else {
            process.stderr.write(
              `[tmux-mcp] SEND confirmed -> socket=${socket} target=${a.target} command=${a.command}\n`,
            );
            await runTmux(socket, [
              "send-keys",
              "-t",
              a.target,
              a.command,
              "C-m",
            ]);
            writeRpc({
              jsonrpc: "2.0",
              id: msg.id,
              result: { content: [{ type: "text", text: "Sent." }] },
            });
          }
        } else {
          writeRpc({
            jsonrpc: "2.0",
            id: msg.id,
            error: { code: -32601, message: "unknown tool" },
          });
        }
      } catch (e: any) {
        writeRpc({
          jsonrpc: "2.0",
          id: msg.id,
          error: { code: -32603, message: String(e?.message || e) },
        });
      }
    }
  }
});
