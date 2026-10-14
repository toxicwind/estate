#!/usr/bin/env bun
// ranch-ui: serves the consolidated ranch dashboard (range/ui/dist) and
// proxies the herd API so the dashboard reaches it same-origin, the way the
// embedded build used to.
//
// The dashboard is served separately from herd (see range/ui/CONSOLIDATION.md):
// it is the tab host over every daemon that serves a page, not a herd view.
// Its apiBase shim (src/lib/apiBase.ts) prefixes herd API paths with
// VITE_HERD_API or window.__HERD_API__, and defaults to same-origin — so this
// server must expose the herd API under the same origin it serves the SPA from.
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
import { join, normalize } from "node:path";

const DIST = process.env.RANCH_UI_DIST ?? "/home/toxic/estate/ranch/range/ui/dist";
const PORT = Number.parseInt(process.env.RANCH_UI_PORT ?? "", 10) || 25205;
const HERD_ORIGIN = process.env.HERD_ORIGIN ?? "http://127.0.0.1:25100";

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

async function proxy(req: Request, target: string): Promise<Response> {
	const init: RequestInit = {
		method: req.method,
		headers: new Headers(req.headers),
	};
	// GET/HEAD must not carry a body; everything else forwards it.
	if (!["GET", "HEAD"].includes(req.method)) init.body = await req.arrayBuffer();
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
			{ error: "upstream unreachable", upstream: HERD_ORIGIN, detail: String(err) },
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
			return Response.json({ ok: true, dist: DIST });
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
			return new Response("dist missing", { status: 503 });
		}

		// Everything else is the herd API surface the dashboard expects
		// same-origin: /v1/*, /api/*, /models/sse, /logs/stream/*, /upstream/*,
		// /comfyui/*, /metrics, /running, /unload, /health-on-herd.
		return proxy(req, HERD_ORIGIN + path);
	},
});

console.log(`ranch-ui on :${PORT} serving ${DIST} (herd ${HERD_ORIGIN})`);
