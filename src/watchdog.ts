import { join, dirname } from "path";
import { mkdirSync, writeFileSync, appendFileSync } from "fs";

const CHECK_INTERVAL = 30000; // 30s
const LOG_FILE = "/home/toxic/sovereign/logs/watchdog.log";
const STATUS_FILE = "/home/toxic/sovereign/logs/watchdog_status.json";

const PROCESSES = {
  "llama-server": { port: 25001, health: "/health" },
  openfang: { port: 25004, health: null },
  yote: { port: 25042, health: "/health" },
};

function log(msg: string) {
  const ts = new Date().toISOString();
  const line = `[${ts}] ${msg}`;
  console.log(line);
  try {
    appendFileSync(LOG_FILE, line + "\n");
  } catch (err) {
    console.error("Failed to write log:", err);
  }
}

async function checkPort(port: number): Promise<boolean> {
  return new Promise((resolve) => {
    const net = require("net");
    const socket = net.connect(port, "127.0.0.1", () => {
      socket.destroy();
      resolve(true);
    });
    socket.on("error", () => {
      resolve(false);
    });
    socket.setTimeout(2000, () => {
      socket.destroy();
      resolve(false);
    });
  });
}

async function main() {
  try {
    mkdirSync(dirname(LOG_FILE), { recursive: true });
  } catch {}
  log("Watchdog started (Bun TS)");

  while (true) {
    const status: Record<string, string> = {};
    for (const [name, cfg] of Object.entries(PROCESSES)) {
      const ok = cfg.health !== null ? await checkPort(cfg.port) : true;
      status[name] = ok ? "healthy" : "down";
      if (!ok) {
        log(`ALERT: ${name} on port ${cfg.port} is DOWN`);
      }
    }
    try {
      writeFileSync(STATUS_FILE, JSON.stringify(status, null, 2));
    } catch (err) {
      console.error("Failed to write status:", err);
    }
    await new Promise((r) => setTimeout(r, CHECK_INTERVAL));
  }
}

const PORT = process.env.PORT ? parseInt(process.env.PORT) : 25022;

Bun.serve({
  port: PORT,
  fetch(req) {
    const url = new URL(req.url);
    if (url.pathname === "/health") {
      return new Response("OK", { status: 200 });
    }
    return new Response("Not Found", { status: 404 });
  },
});

log(`Watchdog HTTP server listening on port ${PORT}`);

main();
