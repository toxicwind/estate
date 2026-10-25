#!/usr/bin/env bun
// ranch-ui: the consolidated ranch dashboard entry point.
//
// It serves the dashboard SPA and proxies the herd API so the dashboard
// reaches it same-origin, the way the embedded build used to.
//
// 2026-10-21 FIX (the "dist missing" 503): the old hardcoded dist path
// (/home/toxic/pens/ranch/range/ui/dist) no longer exists — that build was
// folded into the DelendAI control-plane SPA, which now lives at
// apps/delendai-control-plane and is served by the Vite dev server on :25156.
// The daemon was still pointing at the dead path, so every request to
// :25218 answered "dist missing" and the surface was dead.
//
// Resolution order for the SPA shell (first hit wins):
//   1. $RANCH_UI_DIST                       (explicit override)
//   2. ranch/range/apps/delendai-control-plane/dist   (a real production build)
//   3. proxy the running SPA origin        ($SPA_ORIGIN, default :25156)
//
// The dashboard calls herd at its ROOT paths (/v1/models, /api/profiles,
// /api/mcp, /logs/stream/…, /upstream/…, /comfyui/…), not under /api/herd.
// So the proxy rule is: everything that is not a built asset or the SPA shell
// goes to herd. That is the old embedded behaviour, restored.
//
// Routes:
//   /health      liveness for pitchfork ready_http/health_http (never proxied)
//   /assets/*    hashed build assets (exact-match only)
//   /ui/*        the vite `base` the build emits; stripped before resolving
//   everything else → herd (API, SSE, upstream, comfyui)
import { existsSync, statSync } from "node:fs";
import { join, normalize, extname } from "node:path";

// Herd API surface the dashboard calls at ROOT paths. Everything else with no
// file extension is a client-side route of the SPA and gets the shell.
const HERD_API_PREFIXES = [
  "/v1/",
  "/api/",
  "/models/sse",
  "/logs/stream/",
  "/upstream/",
  "/comfyui/",
  "/metrics",
  "/running",
  "/unload",
  "/health-on-herd",
];

const DIST_CANDIDATES = [
  process.env.RANCH_UI_DIST,
  "/home/toxic/pens/ranch/range/apps/delendai-control-plane/dist",
].filter((p): p is string => Boolean(p));

const DIST =
  DIST_CANDIDATES.find((p) => existsSync(p) && statSync(p).isDirectory()) ??
  DIST_CANDIDATES[0] ??
  "";
const PORT = Number.parseInt(process.env.RANCH_UI_PORT ?? "", 10) || 25205;
const HERD_ORIGIN = process.env.HERD_ORIGIN ?? "http://127.0.0.1:25100";
// The live control-plane SPA (Vite dev server). Proxied when no build exists.
const SPA_ORIGIN =
  process.env.SPA_ORIGIN ??
  process.env.DELENDAI_CONTROL_ORIGIN ??
  "http://127.0.0.1:25156";

const MIME: Record<string, string> = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".ico": "image/x-icon",
  ".woff2": "font/woff2",
  ".woff": "font/woff",
  ".webmanifest": "application/manifest+json",
};

// Prefer the pre-compressed brotli sibling the build emits when the client
// accepts it — the build already paid for compression, so serve it.
function resolve(path: string): string | null {
  const rel = normalize(path).replace(/^(\.\.[/\\])+/, "");
  const abs = join(DIST, rel);
  if (!abs.startsWith(DIST)) return null;
  if (existsSync(abs) && statSync(abs).isFile()) return abs;
  return null;
}

function contentTypeFor(file: string): string {
  const ext = file.slice(file.lastIndexOf("."));
  return MIME[ext] ?? "application/octet-stream";
}

async function proxy(
  req: Request,
  target: string,
  origin: string,
): Promise<Response> {
  const init: RequestInit = {
    method: req.method,
    headers: new Headers(req.headers),
  };
  // GET/HEAD must not carry a body; everything else forwards it.
  if (!["GET", "HEAD"].includes(req.method))
    init.body = await req.arrayBuffer();
  // The proxy adds nothing and removes nothing; the dashboard's own auth
  // headers pass through verbatim.
  try {
    const upstream = await fetch(target, init);
    return new Response(upstream.body, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: upstream.headers,
    });
  } catch (err) {
    return Response.json(
      {
        error: "upstream unreachable",
        upstream: origin,
        detail: String(err),
      },
      { status: 502 },
    );
  }
}

Bun.serve({
  port: PORT,
  // The dashboard is tailnet-only; it binds loopback and tailscale serve
  // fronts it, same as every other estate UI.
  hostname: "127.0.0.1",
  idleTimeout: 255,
  async fetch(req) {
    const path = new URL(req.url).pathname;

    // Liveness probe — never proxied, never cached.
    if (path === "/health") {
      return Response.json({
        ok: true,
        dist: DIST || null,
        mode: DIST && existsSync(DIST) ? "static" : "proxy",
        spa: SPA_ORIGIN,
        herd: HERD_ORIGIN,
      });
    }

    // The build emits absolute URLs under its vite `base` (/ui/), so strip
    // it before resolving; dist itself has no ui/ prefix.
    const rel = path.replace(/^\/ui\//, "/");

    // Hashed build assets are exact-match only. A missing asset is a real
    // 404 (stale index.html referencing a deleted chunk), not a SPA route.
    if (rel.startsWith("/assets/")) {
      const file = resolve(rel);
      if (file) {
        return new Response(Bun.file(file), {
          headers: { "Content-Type": contentTypeFor(file) },
        });
      }
      return new Response("not found", { status: 404 });
    }

    // The SPA shell lives at / and /ui/. Client-side routes have no file
    // extension, so anything file-like that resolved above was an asset;
    // anything else reaching here is an API path heading to herd.
    if (rel === "/" || rel === "/ui" || rel === "/ui/") {
      const file = resolve("/index.html");
      if (file) {
        return new Response(Bun.file(file), {
          headers: { "Content-Type": "text/html; charset=utf-8" },
        });
      }
      // No build on disk: proxy the running control-plane SPA so the
      // dashboard is reachable at :25218 instead of a 503 "dist missing".
      return proxy(req, SPA_ORIGIN + path, SPA_ORIGIN);
    }

    // Deep links into the SPA (e.g. /chats) must resolve to the shell, not
    // to the herd API. A client route has no file extension; the herd API
    // paths below all do, or are explicit prefixes. Without this the Chats
    // view (and every other client route) 404s when pasted into a browser.
    if (
      !HERD_API_PREFIXES.some((p) => path === p || path.startsWith(p)) &&
      !extname(path)
    ) {
      const file = resolve("/index.html");
      if (file) {
        return new Response(Bun.file(file), {
          headers: { "Content-Type": "text/html; charset=utf-8" },
        });
      }
      return proxy(req, SPA_ORIGIN + path, SPA_ORIGIN);
    }

    // Everything else is the herd API surface the dashboard expects
    // same-origin: /v1/*, /api/*, /models/sse, /logs/stream/*, /upstream/*,
    // /comfyui/*, /metrics, /running, /unload, /health-on-herd.
    return proxy(req, HERD_ORIGIN + path, HERD_ORIGIN);
  },
});

console.log(
  `ranch-ui on :${PORT} serving ${DIST || "(no build — proxying the SPA)"} (spa ${SPA_ORIGIN}, herd ${HERD_ORIGIN})`,
);
