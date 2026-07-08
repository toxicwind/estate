import { join } from "path";
import { watch } from "fs";
import { cpus, totalmem } from "os";

const PORT = process.env.PORT ? parseInt(process.env.PORT) : 25080;
const STATIC_DIR = "/home/toxic/sovereign/rust_algo_web/static";

const wsConnections = new Set<any>();

const server = Bun.serve({
  port: PORT,
  websocket: {
    open(ws) {
      wsConnections.add(ws);
    },
    close(ws) {
      wsConnections.delete(ws);
    },
    message(ws, msg) {},
  },
  async fetch(req, server) {
    const url = new URL(req.url);
    let pathname = url.pathname;

    if (pathname === "/ws-reload") {
      if (server.upgrade(req)) return;
      return new Response("Upgrade failed", { status: 400 });
    }

    if (pathname === "/" || pathname === "") {
      pathname = "/index.html";
    }

    if (pathname === "/health") {
      return new Response("OK", { status: 200 });
    }

    if (pathname === "/api/status") {
      const statuses = await checkAllPorts();
      return new Response(JSON.stringify(statuses), {
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    }

    if (pathname === "/api/telemetry") {
      const telemetry = await getSystemTelemetry();
      return new Response(JSON.stringify(telemetry), {
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    }

    try {
      const filePath = join(STATIC_DIR, pathname);
      const file = Bun.file(filePath);
      if (await file.exists()) {
        return new Response(file);
      }
    } catch {}

    return new Response("Not Found", { status: 404 });
  },
});

console.log(`Landing page server listening on port ${PORT}`);

// Watch directories for changes and trigger reload
function watchDir(dirPath: string) {
  try {
    watch(dirPath, { recursive: true }, (event, filename) => {
      console.log(
        `File changed: ${filename || "unknown"} in ${dirPath}. Broadcasting reload...`,
      );
      for (const ws of wsConnections) {
        ws.send("reload");
      }
    });
    console.log(`Watching directory for reload: ${dirPath}`);
  } catch (err) {
    console.error(`Failed to watch ${dirPath}:`, err);
  }
}

watchDir(STATIC_DIR);

async function checkAllPorts() {
  const PORTS: Record<string, number> = {
    "Caddy Edge":    25000,
    "Llama Swap":    25021,
    "OpenFang Core": 25004,
    "Ouroboros":     25005,
    "Prometheus":    25030,
    "HF Downloader": 25020,
    "Watchdog":      25022,
    "Yote Status":   25042,
    "Landing":       25080,
  };

  const results: Record<string, { port: number; online: boolean }> = {};
  await Promise.all(
    Object.entries(PORTS).map(async ([name, port]) => {
      results[name] = {
        port: port,
        online: await checkPort(port),
      };
    }),
  );
  return results;
}

async function checkPort(port: number): Promise<boolean> {
  return new Promise((resolve) => {
    const net = require("net");
    const socket = net.connect(port, "127.0.0.1", () => {
      socket.destroy();
      resolve(true);
    });
    socket.on("error", () => resolve(false));
    socket.setTimeout(200, () => {
      socket.destroy();
      resolve(false);
    });
  });
}

async function getSystemTelemetry() {
  let aiEngine = "Offline";
  try {
    const res = await fetch("http://127.0.0.1:25001/props", {
      signal: AbortSignal.timeout(1000),
    });
    if (res.ok) {
      const data = await res.json();
      const modelPath = data.model_path || "";
      const modelFile = modelPath.split("/").pop() || "";
      aiEngine = modelFile.replace(".gguf", "") || "Llama GGUF";
    }
  } catch (e) {}

  let gpuName = "CPU Only";
  let vramStr = "";
  try {
    const proc = Bun.spawn([
      "nvidia-smi",
      "--query-gpu=gpu_name,memory.total",
      "--format=csv,noheader,nounits",
    ]);
    const output = await new Response(proc.stdout).text();
    if (output && output.includes(",")) {
      const [name, mem] = output.split(",");
      gpuName = name.trim().replace("NVIDIA ", "");
      const vramGb = Math.round(parseInt(mem.trim()) / 1024);
      vramStr = `${vramGb}GB`;
    }
  } catch (e) {}

  let cpuName = "Unknown CPU";
  try {
    const cpuInfo = cpus();
    if (cpuInfo && cpuInfo.length > 0) {
      cpuName = cpuInfo[0].model.trim().replace("(R)", "").replace("(TM)", "");
    }
  } catch (e) {}

  let ramGb = 0;
  try {
    ramGb = Math.round(totalmem() / (1024 * 1024 * 1024));
  } catch (e) {}

  return {
    aiEngine,
    gpuName,
    vramStr,
    cpuName,
    ramGb,
  };
}
