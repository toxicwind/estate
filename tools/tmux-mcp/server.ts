import { spawn } from "child_process";

function writeRpc(res: object) {
  const s = JSON.stringify(res);
  process.stdout.write(`Content-Length: ${Buffer.byteLength(s, "utf8")}\r\n\r\n${s}`);
}

function runTmux(args: string[]): Promise<string> {
  return new Promise((resolve) => {
    const p = spawn("tmux", args);
    let out = "";
    p.stdout.on("data", (d) => (out += d.toString()));
    p.stderr.on("data", (d) => (out += d.toString()));
    p.on("close", () => resolve(out.trim()));
  });
}

const TOOLS = [
  { name: "tmux_list", description: "List active tmux sessions", inputSchema: { type: "object", properties: {} } },
  { name: "tmux_capture", description: "Capture pane scrollback", inputSchema: { type: "object", properties: { target: { type: "string" } }, required: ["target"] } },
  { name: "tmux_send", description: "Send keys/command to pane", inputSchema: { type: "object", properties: { target: { type: "string" }, command: { type: "string" } }, required: ["target", "command"] } }
];

let buf = Buffer.alloc(0);
process.stdin.on("data", async (chunk) => {
  buf = Buffer.concat([buf, chunk]);
  while (true) {
    const idx = buf.indexOf("\r\n\r\n");
    if (idx === -1) break;
    const len = parseInt((buf.subarray(0, idx).toString().match(/Content-Length:\s*(\d+)/i) || [])[1] || "0", 10);
    if (buf.length < idx + 4 + len) break;
    const msg = JSON.parse(buf.subarray(idx + 4, idx + 4 + len).toString());
    buf = buf.subarray(idx + 4 + len);

    if (msg.method === "initialize") {
      writeRpc({ jsonrpc: "2.0", id: msg.id, result: { capabilities: { tools: {} }, serverInfo: { name: "tmux-mcp", version: "1.0" } } });
    } else if (msg.method === "tools/list") {
      writeRpc({ jsonrpc: "2.0", id: msg.id, result: { tools: TOOLS } });
    } else if (msg.method === "tools/call") {
      if (msg.params.name === "tmux_list") {
        const out = await runTmux(["list-sessions"]);
        writeRpc({ jsonrpc: "2.0", id: msg.id, result: { content: [{ type: "text", text: out || "No sessions" }] } });
      } else if (msg.params.name === "tmux_capture") {
        const out = await runTmux(["capture-pane", "-p", "-t", msg.params.arguments.target, "-S", "-100"]);
        writeRpc({ jsonrpc: "2.0", id: msg.id, result: { content: [{ type: "text", text: out }] } });
      } else if (msg.params.name === "tmux_send") {
        await runTmux(["send-keys", "-t", msg.params.arguments.target, msg.params.arguments.command, "C-m"]);
        writeRpc({ jsonrpc: "2.0", id: msg.id, result: { content: [{ type: "text", text: "Sent." }] } });
      }
    }
  }
});
