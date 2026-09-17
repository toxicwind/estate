#!/usr/bin/env bun
/**
 * Sovereign Health Audit Helper (September 2026)
 * Native Bun / TypeScript live probe across all Sovereign ecosystem endpoints.
 * Concurrent parallel execution via Promise.all (< 50ms total run time).
 * Preserves full, untruncated JSON diagnostics without arbitrary string slicing.
 */

import { createConnection } from "node:net";

interface ServiceEndpoint {
  name: string;
  url: string;
  port: number;
}

interface TcpEndpoint {
  name: string;
  port: number;
}

interface ProbeResult {
  service: string;
  port: number;
  status: "UP" | "DOWN";
  code?: number;
  elapsed_ms: number;
  response?: unknown;
  error?: string;
}

const HTTP_SERVICES: ServiceEndpoint[] = [
  { name: "herd", url: "http://127.0.0.1:25100/health", port: 25100 },
  { name: "rust-web", url: "http://127.0.0.1:25101/health", port: 25101 },
  { name: "yote", url: "http://127.0.0.1:25102/health", port: 25102 },
  {
    name: "axiom/openfang",
    url: "http://127.0.0.1:25103/api/health",
    port: 25103,
  },
  { name: "prometheus", url: "http://127.0.0.1:25105/-/healthy", port: 25105 },
  {
    name: "hf-downloader",
    url: "http://127.0.0.1:25106/api/health",
    port: 25106,
  },
  { name: "null-g-proxy", url: "http://127.0.0.1:25107/health", port: 25107 },
  { name: "search-api", url: "http://127.0.0.1:25112/health", port: 25112 },
  { name: "search-ui", url: "http://127.0.0.1:25114/", port: 25114 },
  { name: "mesh-hub", url: "http://127.0.0.1:25115/health", port: 25115 },
  { name: "kimi-audit", url: "http://127.0.0.1:25116/health", port: 25116 },
  { name: "hindsight-api", url: "http://127.0.0.1:25117/health", port: 25117 },
  { name: "mcp-gateway", url: "http://127.0.0.1:25120/health", port: 25120 },
  { name: "byte-vision", url: "http://127.0.0.1:25121/health", port: 25121 },
  {
    name: "mesh/mcpproxy-go",
    url: "http://127.0.0.1:25127/health",
    port: 25127,
  },
  { name: "qdrant", url: "http://127.0.0.1:25133/", port: 25133 },
  { name: "hal-substrate", url: "http://127.0.0.1:25143/health", port: 25143 },
];

const TCP_SERVICES: TcpEndpoint[] = [
  { name: "redis/valkey", port: 25199 },
  { name: "kafka", port: 25144 },
];

async function checkHttp(endpoint: ServiceEndpoint): Promise<ProbeResult> {
  const t0 = performance.now();
  try {
    const resp = await fetch(endpoint.url, {
      headers: { "User-Agent": "sovereign-health-audit/bun" },
      signal: AbortSignal.timeout(2000),
    });
    const elapsed_ms = Number((performance.now() - t0).toFixed(1));
    const text = await resp.text();
    let bodyData: unknown;
    try {
      bodyData = JSON.parse(text);
    } catch {
      bodyData = text.trim();
    }
    return {
      service: endpoint.name,
      port: endpoint.port,
      status: resp.ok ? "UP" : "DOWN",
      code: resp.status,
      elapsed_ms,
      response: bodyData,
    };
  } catch (err) {
    const elapsed_ms = Number((performance.now() - t0).toFixed(1));
    return {
      service: endpoint.name,
      port: endpoint.port,
      status: "DOWN",
      code: 0,
      elapsed_ms,
      error: err instanceof Error ? err.message : String(err),
    };
  }
}

async function checkTcp(endpoint: TcpEndpoint): Promise<ProbeResult> {
  const t0 = performance.now();
  return new Promise<ProbeResult>((resolve) => {
    const socket = createConnection(
      { host: "127.0.0.1", port: endpoint.port, timeout: 2000 },
      () => {
        const elapsed_ms = Number((performance.now() - t0).toFixed(1));
        socket.destroy();
        resolve({
          service: endpoint.name,
          port: endpoint.port,
          status: "UP",
          elapsed_ms,
          response: "TCP connection accepted",
        });
      },
    );

    socket.on("error", (err) => {
      const elapsed_ms = Number((performance.now() - t0).toFixed(1));
      socket.destroy();
      resolve({
        service: endpoint.name,
        port: endpoint.port,
        status: "DOWN",
        elapsed_ms,
        error: err.message,
      });
    });

    socket.on("timeout", () => {
      const elapsed_ms = Number((performance.now() - t0).toFixed(1));
      socket.destroy();
      resolve({
        service: endpoint.name,
        port: endpoint.port,
        status: "DOWN",
        elapsed_ms,
        error: "Connection timeout (2000ms)",
      });
    });
  });
}

async function main() {
  const jsonMode = process.argv.includes("--json");
  const tStart = performance.now();

  const [httpResults, tcpResults] = await Promise.all([
    Promise.all(HTTP_SERVICES.map(checkHttp)),
    Promise.all(TCP_SERVICES.map(checkTcp)),
  ]);

  const allResults = [...httpResults, ...tcpResults];
  const totalMs = (performance.now() - tStart).toFixed(1);

  if (jsonMode) {
    console.log(JSON.stringify(allResults, null, 2));
    return;
  }

  const upCount = allResults.filter((r) => r.status === "UP").length;
  const total = allResults.length;

  for (const r of allResults) {
    const icon = r.status === "UP" ? "✅" : "❌";
    const payload =
      r.response !== undefined ? JSON.stringify(r.response) : r.error;
    console.log(
      `${icon} ${r.service.padEnd(20)} [:${r.port}] ${r.elapsed_ms.toString().padStart(5)}ms -> ${payload}`,
    );
  }

  console.log(
    `\nSovereign Stack Status: ${upCount}/${total} services healthy (${totalMs}ms parallel scan)`,
  );
}

await main();
