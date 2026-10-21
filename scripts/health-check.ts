#!/usr/bin/env bun
/**
 * Robust Estate Health Check - Pure TypeScript
 * Verifies live HTTP endpoints across all configured 25xxx services without bash/curl pipelines.
 */
import { parsePortsEnv } from "../src/utils/ports.ts";
import { resolve } from "node:path";
import { createConnection } from "node:net";

const ROOT = resolve(import.meta.dir, "..");
const portsMap = parsePortsEnv(ROOT);

// Essential core services mapped to their ports (derived from ports.env or defaults)
const SERVICES: Record<string, number> = {
  "herd": portsMap.get("LLAMA_SWAP_PORT") ?? 25100,
  "qdrant": portsMap.get("QDRANT_PORT") ?? 25133,
  "redis": portsMap.get("REDIS_PORT") ?? 25203,
  "yote-core": portsMap.get("YOTE_CORE_PORT") ?? portsMap.get("COYOTE_PORT") ?? 25143,
  "yote-relay": portsMap.get("YOTE_RELAY_PORT") ?? portsMap.get("YOTE_PORT") ?? 25102,
  "prometheus": portsMap.get("PROMETHEUS_PORT") ?? 25105,
  "grafana": portsMap.get("GRAFANA_PORT") ?? 25110,
  "nativelink": portsMap.get("NATIVELINK_FRONTEND_PORT") ?? 25155,
  "gatehouse": portsMap.get("GATEHOUSE_PORT") ?? 25127,
};

const HEALTH_PATHS = ["/health", "/-/healthy", "/api/health", "/"];

let failedCount = 0;

for (const [svc, port] of Object.entries(SERVICES)) {
  let isHealthy = false;

  if (svc === "redis") {
    // Redis/Valkey speaks RESP protocol, not HTTP
    isHealthy = await new Promise<boolean>((resolve) => {
      const socket = createConnection({ port, host: "127.0.0.1", timeout: 1000 }, () => {
        socket.write("*1\r\n$4\r\nPING\r\n");
      });
      socket.on("data", (data) => {
        if (data.toString().includes("PONG")) {
          isHealthy = true;
          socket.end();
          resolve(true);
        }
      });
      socket.on("error", () => {
        socket.destroy();
        resolve(false);
      });
      socket.on("timeout", () => {
        socket.destroy();
        resolve(false);
      });
    });
  } else {
    for (const path of HEALTH_PATHS) {
      try {
        const url = `http://127.0.0.1:${port}${path}`;
        const res = await fetch(url, {
          method: "GET",
          signal: AbortSignal.timeout(1500),
        });
        if (res.ok || res.status === 401 || res.status === 403 || res.status === 404) {
          // HTTP responder alive
          isHealthy = true;
          break;
        }
      } catch {
        // try next path
      }
    }
  }

  if (!isHealthy) {
    console.log(`❌ ${svc} unhealthy on port ${port}`);
    failedCount++;
  } else {
    console.log(`✔ ${svc} healthy on port ${port}`);
  }
}

if (failedCount > 0) {
  try {
    await fetch("https://ntfy.sh/estate-alerts", {
      method: "POST",
      body: `Stack degraded: ${failedCount} services unreachable`,
      signal: AbortSignal.timeout(2000),
    });
  } catch {
    // best effort alert
  }
  process.exit(1);
}

console.log("All checked estate services healthy.");
process.exit(0);
