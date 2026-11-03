#!/usr/bin/env bun
// moment-interim-serve.ts — interim surface for agentic-moment while the
// moment.mildlyawesome.com zone is hijacked (P0: attacker-owned CF account).
// Serves the site content dir over HTTP with an index page.
// Usage: bun moment-interim-serve.ts [port]   (default 25261 — 25260 is
// squatted by selenite; discovered live 2026-11-02)
import { readdirSync, readFileSync, existsSync, statSync } from "node:fs";
import { join, extname } from "node:path";

const SITE = "/home/toxic/pens/agentic-moment/products/site";
const PORT = Number(process.argv[2] ?? 25261);

const MIME: Record<string, string> = {
	".html": "text/html; charset=utf-8",
	".md": "text/plain; charset=utf-8",
	".json": "application/json",
	".js": "text/javascript",
	".css": "text/css",
	".png": "image/png",
	".svg": "image/svg+xml",
	".jpg": "image/jpeg",
};

function listDir(rel: string): string {
	const abs = join(SITE, rel);
	if (!existsSync(abs) || !statSync(abs).isDirectory()) return "";
	const items = readdirSync(abs, { withFileTypes: true })
		.filter(e => !e.name.startsWith("."))
		.map(e => {
			const href = rel === "." ? e.name : `${rel}/${e.name}`;
			const label = e.isDirectory() ? `${e.name}/` : e.name;
			return `<li><a href="/${href}">${label}</a></li>`;
		})
		.join("\n");
	return `<!DOCTYPE html><html><head><meta charset="utf-8"><title>agentic-moment (interim)</title><style>body{font-family:ui-monospace,monospace;max-width:760px;margin:3rem auto;padding:0 1rem;background:#0d1117;color:#e6edf3}a{color:#58a6ff}h1{font-size:1.3rem}small{color:#8b949e}</style></head><body><h1>agentic-moment — interim surface</h1><small>moment.mildlyawesome.com hijack is CONTAINED (2026-11-02: attacker demoted to read-only, all 8 zones deleted from the attacker-owned account — the 301s are dead edge-wide). Canonical: <a href="https://toxicwind.github.io/agentic-moment-2026/">toxicwind.github.io/agentic-moment-2026</a>. The vanity host returns after zone re-add on a clean account.</small><ul>${items}</ul></body></html>`;
}

Bun.serve({
	port: PORT,
	fetch(req) {
		const url = new URL(req.url);
		let rel = decodeURIComponent(url.pathname).replace(/^\/+/, "") || ".";
		const abs = join(SITE, rel);
		if (existsSync(abs) && statSync(abs).isDirectory()) {
			const idx = join(abs, "index.html");
			if (existsSync(idx)) {
				return new Response(readFileSync(idx), { headers: { "Content-Type": MIME[".html"] } });
			}
			return new Response(listDir(rel), { headers: { "Content-Type": MIME[".html"] } });
		}
		if (existsSync(abs) && statSync(abs).isFile()) {
			const type = MIME[extname(abs)] ?? "application/octet-stream";
			return new Response(readFileSync(abs), { headers: { "Content-Type": type } });
		}
		return new Response("not found", { status: 404 });
	},
});
console.log(`moment-interim serving ${SITE} on :${PORT}`);
