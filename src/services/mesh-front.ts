#!/usr/bin/env bun
/**
 * mesh-front — Thin reverse proxy that adds mesh routing and a standard /health endpoint.
 * Usage: bun run mesh-front.ts --service <name> --listen <host:port> --backend <host:port>
 */
import { handleMeshRequest } from "../lib/ghas-mesh-features.ts";

// Parse --service <name> --listen <host:port> --backend <host:port>
function parseArgs(): Record<string, string> {
  const args = process.argv.slice(2);
  const result: Record<string, string> = {};
  for (let i = 0; i < args.length; i++) {
    if (args[i].startsWith("--")) {
      const key = args[i].slice(2);
      result[key] = args[i + 1] || "";
      i++;
    }
  }
  return result;
}

const args = parseArgs();
const service = args.service || "unknown";
const listenHost = args.listen?.split(":")[0] || "0.0.0.0";
const listenPort = parseInt(args.listen?.split(":")[1] || "0", 10);
const backend = args.backend || "127.0.0.1:0";

const backendBase = backend.startsWith("http") ? backend : `http://${backend}`;

// Per-service health endpoint mapping
const healthEndpoints: Record<string, string> = {
  "llama-swap": "/health",
  "rust-web": "/health",
  openfang: "/api/health",
  prometheus: "/-/healthy",
  "hf-downloader": "/health",
  grafana: "/api/health",
  "null-g-proxy": "/health",
  "ghas-api": "/health",
  "ghas-mcp": "/health",
  "byte-vision": "/mcp-completion",
};

const healthEndpoint = healthEndpoints[service] || "/health";

console.log(
  `[mesh-front] service=${service} listen=${listenHost}:${listenPort} backend=${backendBase} health=${healthEndpoint}`,
);

const server = Bun.serve({
  hostname: listenHost,
  port: listenPort,
  idleTimeout: 255,
  async fetch(req) {
    const u = new URL(req.url);

    // Health check - route to service-specific endpoint
    if (u.pathname === "/health") {
      const res = await fetch(`${backendBase}${healthEndpoint}`, {
        signal: AbortSignal.timeout(10_000),
        method: healthEndpoint === "/mcp-completion" ? "POST" : "GET",
        headers:
          healthEndpoint === "/mcp-completion"
            ? {
                "Content-Type": "application/json",
              }
            : {},
        body:
          healthEndpoint === "/mcp-completion"
            ? JSON.stringify({
                jsonrpc: "2.0",
                method: "initialize",
                params: {
                  protocolVersion: "2024-11-05",
                  capabilities: {},
                  clientInfo: { name: "health-check", version: "1" },
                },
                id: 1,
              })
            : undefined,
      });
      const buf = await res.arrayBuffer();
      return new Response(buf, {
        status: res.status,
        headers: { "content-type": "application/json" },
      });
    }

    // Mesh feature routing
    if (u.pathname.startsWith("/mesh")) {
      const m = await handleMeshRequest(req, {
        service: service as any,
        version: `mesh-front/${service}`,
      });
      if (m) return m;
    }

    // Proxy everything else to backend
    const target = `${backendBase}${u.pathname}${u.search}`;
    const headers = new Headers(req.headers);
    headers.delete("host");
    headers.set("accept-encoding", "identity");
    const res = await fetch(target, {
      method: req.method,
      headers,
      body: req.body,
    });
    return res;
  },
});

console.log(
  `[mesh-front] ${service} listening on ${server.hostname}:${server.port} -> ${backendBase}`,
);
