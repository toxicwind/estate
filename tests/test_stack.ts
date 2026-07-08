#!/usr/bin/env bun
import { existsSync, readFileSync } from "fs";
import { join } from "path";

const SOV_ROOT = process.env.SOVEREIGN_ROOT || "/home/toxic/sovereign";
const PORTS_FILE = join(SOV_ROOT, "stack", "ports.env");

// Parse ports.env for dynamic discovery
function getPorts(): Record<string, number> {
  const envContent = readFileSync(PORTS_FILE, "utf-8");
  const ports: Record<string, number> = {};
  const lines = envContent.split("\n");
  for (const line of lines) {
    if (line.startsWith("export")) {
      const match = line.match(/export\s+(\w+)=(\d+)/);
      if (match) ports[match[1]] = parseInt(match[2], 10);
    }
  }
  return ports;
}

const P = getPorts();

// Mapping service IDs to their specific readiness paths
const REGISTRY: Record<string, string[]> = {
  "LLAMA_HERDER": ["/health"],
  "OPENFANG_PORT": ["/api/health"],
  "RUST_WEB_PORT": ["/health"],
  "YOTE_PORT": ["/health"],
  "HF_DOWNLOADER": ["/"],
  "WATCHDOG_PORT": ["/health"],
  "LANDING_PORT": ["/health"],
};

const BASE = "http://127.0.0.1";
const green = (s: string) => `\x1b[92m${s}\x1b[0m`;
const red = (s: string) => `\x1b[91m${s}\x1b[0m`;

async function probe(name: string, port: number, paths: string[]) {
  for (const path of paths) {
    try {
      const res = await fetch(`${BASE}:${port}${path}`, {
        signal: AbortSignal.timeout(1500),
      });
      if (res.ok) return [true, `${res.status} ${path}`] as const;
    } catch {}
  }
  return [false, "unresponsive"] as const;
}

console.log(`🚀 Sovereign Stack Health — ${new Date().toLocaleTimeString()}`);
console.log("-".repeat(55));

let healthyCount = 0;
const entries = Object.entries(REGISTRY);

for (const [envVar, paths] of entries) {
  const port = P[envVar];
  if (!port) continue;
  
  const [ok, msg] = await probe(envVar, port, paths);
  healthyCount += ok ? 1 : 0;
  
  const status = ok ? green("✓") : red("✗");
  console.log(`${status} ${envVar.padEnd(15)} :${String(port).padEnd(5)} → ${msg}`);
}

console.log("-".repeat(55));
process.exit(healthyCount === entries.length ? 0 : 1);