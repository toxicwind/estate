/**
 * Mock `kimi web` backend for gateway integration testing.
 * Usage: mock-backend.ts --port <n>
 * Prints a kimi-style banner, then serves a tiny kap-server lookalike.
 */
const args = process.argv.slice(2);
const portIdx = args.indexOf("--port");
const port = portIdx >= 0 ? Number(args[portIdx + 1]) : 0;
const BACKEND_TOKEN = "mock-backend-token";

console.log(`Local:   http://127.0.0.1:${port}/#token=${BACKEND_TOKEN}`);
console.log(`Token: ${BACKEND_TOKEN}`);
console.log(`Stop:    Ctrl+C`);

Bun.serve({
	hostname: "127.0.0.1",
	port,
	fetch(req, server) {
		const url = new URL(req.url);
		const upgrade = req.headers.get("upgrade")?.toLowerCase();
		if (upgrade === "websocket") {
			const proto = req.headers.get("sec-websocket-protocol") ?? "";
			if (!proto.includes(`kimi-code.bearer.${BACKEND_TOKEN}`)) {
				return new Response("unauthorized", { status: 401 });
			}
			const ok = server.upgrade(req, {
				headers: { "Sec-WebSocket-Protocol": proto },
			});
			if (!ok) return new Response("upgrade failed", { status: 500 });
			return undefined as unknown as Response;
		}
		if (url.pathname === "/") {
			return new Response(
				`<html><head><script src="/boot.js"></script></head><body>mock-kimi-ui</body></html>`,
				{ headers: { "content-type": "text/html" } },
			);
		}
		if (url.pathname === "/boot.js") {
			return new Response(`/* mock boot */`, {
				headers: { "content-type": "text/javascript" },
			});
		}
		if (url.pathname === "/api/v1/ping") {
			const auth = req.headers.get("authorization");
			if (auth !== `Bearer ${BACKEND_TOKEN}`) {
				return new Response("unauthorized", { status: 401 });
			}
			if (url.searchParams.has("token")) {
				return new Response("token leaked in query", { status: 500 });
			}
			return Response.json({ ok: true, pong: true });
		}
		return new Response("not found", { status: 404 });
	},
	websocket: {
		message(ws, msg) {
			ws.send(`echo:${msg}`);
		},
	},
});
