#!/usr/bin/env bun
/**
 * Mesh front: reverse-proxy a backend while serving /mesh/* (20 GHAS features)
 * on the public service port. Used for binary daemons that cannot mount routes.
 *
 * Usage:
 *   bun run src/services/mesh-front.ts \
 *     --service llama-swap --listen 0.0.0.0:25100 --backend 127.0.0.1:26100
 *
 * Or with --spawn: start backend cmd on --backend port, then front on --listen.
 */
import {
  handleMeshRequest,
  type MeshServiceId,
} from "../lib/ghas-mesh-features.ts";
import { loadSovereignPorts } from "../lib/ports.ts";

loadSovereignPorts();

function arg(name: string, fallback = ""): string {
  const i = process.argv.indexOf(name);
  if (i >= 0 && process.argv[i + 1]) return process.argv[i + 1];
  return fallback;
}

const service = (arg("--service") || process.env.MESH_SERVICE || "mesh-hub") as MeshServiceId;
const listen = arg("--listen") || process.env.MESH_LISTEN || "127.0.0.1:25115";
const backend = arg("--backend") || process.env.MESH_BACKEND || "";
const [listenHost, listenPortStr] = listen.includes(":")
  ? listen.split(":")
  : ["127.0.0.1", listen];
const listenPort = Number(listenPortStr);

if (!backend) {
  console.error("mesh-front requires --backend host:port");
  process.exit(2);
}

const backendBase = backend.startsWith("http")
  ? backend
  : `http://${backend}`;

const server = Bun.serve({
  hostname: listenHost === "0.0.0.0" ? "0.0.0.0" : listenHost,
  port: listenPort,
  // Long agent chats (OpenFang/llama load) need a high idle timeout
  idleTimeout: 255,
  async fetch(req) {
    const u = new URL(req.url);
    // Alias bare /health -> backend /api/health (binary only serves /api/health)
    if (u.pathname === "/health") {
      const res = await fetch(`${backendBase}/api/health`, {
        signal: AbortSignal.timeout(10_000),
      });
      const buf = await res.arrayBuffer();
      return new Response(buf, {
        status: res.status,
        headers: { "content-type": "application/json" },
      });
    }
    if (u.pathname.startsWith("/mesh")) {
      const m = await handleMeshRequest(req, {
        service,
        version: `mesh-front/${service}`,
      });
      if (m) return m;
    }

    // Proxy everything else to backend
    const target = `${backendBase}${u.pathname}${u.search}`;
    try {
      const headers = new Headers(req.headers);
      headers.delete("host");
      // Avoid brotli double-decode issues through the front
      headers.set("accept-encoding", "identity");
      const init: RequestInit & { signal?: AbortSignal } = {
        method: req.method,
        headers,
        body:
          req.method === "GET" || req.method === "HEAD"
            ? undefined
            : await req.arrayBuffer(),
        // @ts-expect-error bun duplex
        duplex: "half",
        signal: AbortSignal.timeout(240_000),
      };
      const res = await fetch(target, init);
      // Buffer non-stream responses so long chat JSON is not cut mid-proxy
      const path = u.pathname;
      if (
        path.includes("/v1/chat/completions") ||
        path.includes("/api/")
      ) {
        const buf = await res.arrayBuffer();
        const outHeaders = new Headers(res.headers);
        outHeaders.delete("content-encoding");
        outHeaders.delete("transfer-encoding");
        outHeaders.set("content-length", String(buf.byteLength));
        return new Response(buf, { status: res.status, headers: outHeaders });
      }
      return new Response(res.body, {
        status: res.status,
        headers: res.headers,
      });
    } catch (e) {
      return new Response(
        JSON.stringify({
          error: "backend_down",
          backend: backendBase,
          detail: String(e),
        }),
        { status: 502, headers: { "content-type": "application/json" } },
      );
    }
  },
});

console.log(
  `[mesh-front] service=${service} listen=${listenHost}:${server.port} backend=${backendBase}`,
);
