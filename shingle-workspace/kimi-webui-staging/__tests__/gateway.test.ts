/**
 * Gateway integration test against the mock backend.
 * Run: MOCK_BACKEND_TS=/path/to/mock-backend.ts bun test gateway.test.ts
 * (skips if MOCK_BACKEND_TS is unset or no kimi-style backend is available)
 */
import { describe, expect, test } from "bun:test";
import { KimiWebGateway } from "../src/web.ts";

const MOCK_BACKEND_TS = process.env.MOCK_BACKEND_TS;
const MOCK_SH = process.env.MOCK_KIMI_SH;

describe("KimiWebGateway (mock backend)", () => {
	test("full lifecycle: start, proxy, auth, WS relay, stop", async () => {
		if (!MOCK_BACKEND_TS || !MOCK_SH) {
			console.log("skipping gateway integration test (no mock backend)");
			return;
		}
		const gw = new KimiWebGateway({
			binary: MOCK_SH,
			cwd: "/tmp",
			port: 39631,
			env: { MOCK_BACKEND_TS },
			onLog: () => {},
		});

		const info = await gw.start();
		expect(info.url).toMatch(/^http:\/\/127\.0\.0\.1:\d+\/tau\/\?token=/);
		expect(info.backend.token).toBe("mock-backend-token");
		const base = `http://127.0.0.1:${info.gatewayPort}`;

		// Shell requires the gateway token…
		const noAuth = await fetch(`${base}/tau/`);
		expect(noAuth.status).toBe(401);

		const shell = await fetch(info.url);
		expect(shell.status).toBe(200);
		const shellHtml = await shell.text();
		expect(shellHtml).toContain('id="pane-kimi"');
		expect(shellHtml).toContain(info.token);

		// …but the kimi UI root proxies through (loopback-open like `kimi web`).
		const ui = await fetch(`${base}/`);
		expect(ui.status).toBe(200);
		expect(await ui.text()).toContain("mock-kimi-ui");

		// API routes need the gateway token, swapped to the backend token upstream.
		const apiNoAuth = await fetch(`${base}/api/v1/ping`);
		expect(apiNoAuth.status).toBe(401);

		const api = await fetch(`${base}/api/v1/ping?token=${info.token}`, {
			headers: { authorization: `Bearer ${info.token}` },
		});
		expect(api.status).toBe(200);
		expect(await api.json()).toEqual({ ok: true, pong: true });

		// WebSocket relay: gateway token in, backend token upstream.
		const ws = new WebSocket(
			`ws://127.0.0.1:${info.gatewayPort}/ws?token=${info.token}`,
			[`kimi-code.bearer.${info.token}`],
		);
		const echoed = await new Promise<string>((resolve, reject) => {
			const timer = setTimeout(() => reject(new Error("ws timeout")), 5000);
			ws.onopen = () => ws.send("hello");
			ws.onmessage = (ev) => {
				clearTimeout(timer);
				resolve(String(ev.data));
			};
			ws.onerror = () => {
				clearTimeout(timer);
				reject(new Error("ws error"));
			};
		});
		expect(echoed).toBe("echo:hello");
		ws.close();

		// WS without the token is rejected.
		const bad = new WebSocket(`ws://127.0.0.1:${info.gatewayPort}/ws`, [
			"kimi-code.bearer.wrong",
		]);
		const badResult = await new Promise<string>((resolve) => {
			const timer = setTimeout(() => resolve("timeout"), 3000);
			bad.onerror = () => {
				clearTimeout(timer);
				resolve("rejected");
			};
			bad.onopen = () => {
				clearTimeout(timer);
				resolve("opened");
			};
		});
		expect(badResult).not.toBe("opened");
		try {
			bad.close();
		} catch {
			/* ignore */
		}

		await gw.stop();
		expect(gw.running).toBe(false);
	}, 30_000);
});
