import { join } from "path";
import { watch } from "fs";
import { cpus, totalmem } from "os";
import net from "net";

const PORT = parseInt(process.env.PORT || "25080");
const STATIC_DIR = process.env.STATIC_DIR || "/home/toxic/sovereign/rust_algo_web/static";

const wsConnections = new Set<WebSocket>();
let reloadDebounce: ReturnType<typeof setTimeout> | null = null;

const server = Bun.serve({
  port: PORT,
  websocket: {
    open(ws) { wsConnections.add(ws); },
    close(ws) { wsConnections.delete(ws); },
    message() {}
  },
  async fetch(req, s) {
    const url = new URL(req.url);
    let pathname = url.pathname;

    if (pathname === "/ws-reload") {
      if (s.upgrade(req)) return;
      return new Response("Upgrade failed", { status: 400 });
    }
    if (pathname === "/health") return new Response("OK");

    if (pathname === "/api/status") {
      const statuses = await checkAllPorts();
      return Response.json(statuses, { headers: { "Access-Control-Allow-Origin": "*" } });
    }
    if (pathname === "/api/telemetry") {
      const t = await getSystemTelemetry();
      return Response.json(t, { headers: { "Access-Control-Allow-Origin": "*" } });
    }

    // secure: prevent../../../
    if (pathname === "/" || pathname === "") pathname = "/index.html";
    const safePath = pathname.replace(/\.\./g, "").replace(/\/\//g, "/");

    try {
      const filePath = join(STATIC_DIR, safePath);
      if (!filePath.startsWith(STATIC_DIR)) return new Response("Forbidden", { status: 403 });
      const file = Bun.file(filePath);
      if (await file.exists()) return new Response(file);
    } catch {}

    return new Response("Not Found", { status: 404 });
  },
});

console.log(`Landing listening on :${PORT}`);

function watchDir(dirPath: string) {
  try {
    watch(dirPath, { recursive: true }, () => {
      if (reloadDebounce) return;
      reloadDebounce = setTimeout(() => {
        console.log(`Reload broadcast`);
        for (const ws of wsConnections) ws.send("reload");
        reloadDebounce = null;
      }, 300) as NodeJS.Timeout;
    });
  } catch (e) { console.error(`watch fail ${dirPath}`, e); }
}
watchDir(STATIC_DIR);

const PORTS: Record<string, number> = {
  "Llama Swap": 28080,
  "OpenFang": 25004,
  "Rust Dash": 25005,
  "Prometheus": 25030,
  "Watchdog": 25022,
  "Yote": 25042,
  "Landing": 25080,
};

async function checkAllPorts() {
  const results: Record<string, { port: number; online: boolean }> = {};
  await Promise.all(Object.entries(PORTS).map(async ([name, port]) => {
    results[name] = { port, online: await checkPort(port) };
  }));
  return results;
}

function checkPort(port: number): Promise<boolean> {
  return new Promise((res) => {
    const socket = net.connect(port, "127.0.0.1", () => { socket.destroy(); res(true); });
    socket.on("error", () => res(false));
    socket.setTimeout(200, () => { socket.destroy(); res(false); });
  });
}

async function getSystemTelemetry() {
  let aiEngine = "Offline";
  try {
    const r = await fetch(`http://127.0.0.1:28080/health`, { signal: AbortSignal.timeout(1000) });
    if (r.ok) aiEngine = "Llama Swap Active";
  } catch {}

  let gpuName = "CPU Only", vramStr = "";
  try {
    const proc = Bun.spawn(["nvidia-smi", "--query-gpu=gpu_name,memory.total", "--format=csv,noheader,nounits"]);
    const out = await new Response(proc.stdout).text();
    if (out.includes(",")) {
      const [name, mem] = out.split(",");
      gpuName = name.trim().replace("NVIDIA ", "");
      vramStr = `${Math.round(parseInt(mem.trim())/1024)}GB`;
    }
  } catch {}

  return {
    aiEngine,
    gpuName,
    vramStr,
    cpuName: cpus()[0]?.model.replace("(R)","").replace("(TM)","") || "Unknown",
    ramGb: Math.round(totalmem() / 1024 / 1024),
  };
}