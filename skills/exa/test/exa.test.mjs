// End-to-end contract tests for the exa CLI's credential path.
//
// A real unix-socket authd is started per case (no authd on this box), the
// outbound fetch is stubbed, and the shipped code is exercised unmodified —
// there is deliberately no env override for the base URL, because a backdoor
// that redirects a credentialed client is the thing we least want.
import { afterAll, beforeAll, describe, expect, test } from "bun:test";
import { createServer } from "node:http";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import {
  DynamicCredentialError,
  ensureAllowedUrl,
  surrogateHeaders,
} from "../bin/dynamic-credentials.mjs";

const BIN = join(import.meta.dir, "..", "bin");
const SOCK = join(mkdtempSync(join(tmpdir(), "authd-")), "authd.sock");
process.env.JARVIS_AUTHD_SOCK = SOCK;

const SURROGATE = "hsurr:0123456789abcdef0123456789abcdef";

let mode = "ok";
let lastRequest = null;

const authd = createServer((req, res) => {
  let body = "";
  req.on("data", (c) => (body += c));
  req.on("end", () => {
    if (req.url !== "/v1/credentials/surrogate") return void res.writeHead(404).end();
    const say = (o) => res.writeHead(200, { "Content-Type": "application/json" }).end(JSON.stringify(o));
    if (mode === "missing") return void say({ credentials: [{ name: "refresh_token" }] });
    if (mode === "realsecret")
      return void say({ credentials: [{ name: "access_token", surrogate: "sk-real-leaked" }] });
    if (mode === "boom") return void res.writeHead(500).end("{}");
    if (mode === "queryparam")
      return void say({
        credentials: [
          { name: "access_token", surrogate: SURROGATE, placement: { query_param: "api_key" } },
        ],
      });
    if (mode === "notjson") return void say({ credentials: "nope" });
    say({ credentials: [{ name: "access_token", surrogate: SURROGATE, placement: "bearer_header" }] });
  });
});

beforeAll(() => new Promise((r) => authd.listen(SOCK, r)));
afterAll(() => {
  authd.close();
  rmSync(join(SOCK, ".."), { recursive: true, force: true });
});

function stubFetch(response) {
  globalThis.fetch = async (url, init) => {
    lastRequest = { url, init };
    return response;
  };
}

const okResponse = () =>
  new Response(JSON.stringify({ results: [], costDollars: { total: 0.01 } }), { status: 200 });

describe("surrogate injection", () => {
  test("sends only the hsurr surrogate as a bearer header", async () => {
    mode = "ok";
    const h = await surrogateHeaders("https://api.exa.ai/search", "custom.exa", {
      allowedHosts: ["api.exa.ai"],
    });
    expect(h.Authorization).toBe(`Bearer ${SURROGATE}`);
    expect(JSON.stringify(h)).not.toContain("sk-real");
  });

  test("refuses a host outside the allowlist", () => {
    expect(() =>
      ensureAllowedUrl("https://evil.example.com/search", ["api.exa.ai"]),
    ).toThrow(DynamicCredentialError);
  });

  test("refuses before any socket call, so nothing leaks to a rogue host", async () => {
    mode = "ok";
    await expect(
      surrogateHeaders("https://evil.example.com/x", "custom.exa", {
        allowedHosts: ["api.exa.ai"],
      }),
    ).rejects.toThrow(/refusing authenticated request to evil.example.com/);
  });

  test("missing authd socket is reported as unavailable", async () => {
    const saved = process.env.JARVIS_AUTHD_SOCK;
    process.env.JARVIS_AUTHD_SOCK = join(tmpdir(), "definitely-not-a-socket.sock");
    const mod = await import(`../bin/dynamic-credentials.mjs?bust=${Date.now()}`);
    await expect(
      mod.dynamicCredentialEntry("custom.exa", "access_token", {
        socketPath: process.env.JARVIS_AUTHD_SOCK,
      }),
    ).rejects.toThrow(/unavailable: authd socket not found/);
    process.env.JARVIS_AUTHD_SOCK = saved;
  });

  test("falls back to the local store when the broker socket is absent", async () => {
    const savedSock = process.env.JARVIS_AUTHD_SOCK;
    const savedSmith = process.env.SECRETSMITH;
    const store = mkdtempSync(join(tmpdir(), "secrets-"));
    const fake = join(store, "fake-secretsmith");
    writeFileSync(fake, "#!/bin/sh\necho '{\"name\":\"custom.exa\",\"key\":\"EXA_API_KEY\",\"value\":\"local-real-key\"}'\n", { mode: 0o755 });
    process.env.SECRETSMITH = fake;
    process.env.JARVIS_AUTHD_SOCK = join(store, "absent.sock");
    const mod = await import(`../bin/dynamic-credentials.mjs?bust=${Date.now()}`);
    const headers = await mod.surrogateHeaders(
      "https://api.exa.ai/search",
      "custom.exa",
      { allowedHosts: ["api.exa.ai"] },
    );
    expect(headers.Authorization).toBe("Bearer local-real-key");
    process.env.JARVIS_AUTHD_SOCK = savedSock;
    process.env.SECRETSMITH = savedSmith;
    rmSync(store, { recursive: true, force: true });
  });

  test("still reports unavailable when neither broker nor store has the key", async () => {
    const savedSock = process.env.JARVIS_AUTHD_SOCK;
    const savedSmith = process.env.SECRETSMITH;
    const store = mkdtempSync(join(tmpdir(), "secrets-empty-"));
    const empty = join(store, "empty-secretsmith");
    writeFileSync(empty, "#!/bin/sh\nexit 1\n", { mode: 0o755 });
    process.env.SECRETSMITH = empty;
    process.env.JARVIS_AUTHD_SOCK = join(store, "absent.sock");
    const mod = await import(`../bin/dynamic-credentials.mjs?bust=${Date.now()}`);
    await expect(
      mod.surrogateHeaders("https://api.exa.ai/search", "custom.exa", {
        allowedHosts: ["api.exa.ai"],
      }),
    ).rejects.toThrow(/unavailable: authd socket not found/);
    process.env.JARVIS_AUTHD_SOCK = savedSock;
    process.env.SECRETSMITH = savedSmith;
    rmSync(store, { recursive: true, force: true });
  });
});

describe("authd failure modes", () => {
  const cases = [
    ["missing", /missing access_token surrogate/],
    ["realsecret", /non-surrogate value/],
    ["boom", /returned HTTP 500/],
    ["notjson", /credentials: "nope"|missing access_token surrogate/],
    ["queryparam", /query_param credentials must be applied/],
  ];
  for (const [m, re] of cases) {
    test(`mode=${m} surfaces a typed error`, async () => {
      mode = m;
      await expect(
        surrogateHeaders("https://api.exa.ai/search", "custom.exa", {
          allowedHosts: ["api.exa.ai"],
        }),
      ).rejects.toThrow(re);
    });
  }
});

describe("exa CLI", () => {
  test("search posts an authenticated JSON request", async () => {
    mode = "ok";
    stubFetch(okResponse());
    const { post } = await import("../bin/exa.mjs");
    const out = await post("/search", { query: "hyprland", numResults: 3 });
    expect(lastRequest.url).toBe("https://api.exa.ai/search");
    expect(lastRequest.init.headers.Authorization).toBe(`Bearer ${SURROGATE}`);
    expect(JSON.parse(lastRequest.init.body)).toEqual({ query: "hyprland", numResults: 3 });
    expect(out.costDollars.total).toBe(0.01);
  });

  test("a provider 500 is an error, not a silent success", async () => {
    mode = "ok";
    stubFetch(new Response(JSON.stringify({ error: "upstream" }), { status: 500 }));
    const { post } = await import("../bin/exa.mjs");
    await expect(post("/search", { query: "x" })).rejects.toThrow(/HTTP 500/);
  });

  test("non-JSON provider body is a typed credential error", async () => {
    mode = "ok";
    stubFetch(new Response("<html>gateway</html>", { status: 200 }));
    const { post } = await import("../bin/exa.mjs");
    await expect(post("/search", { query: "x" })).rejects.toThrow(
      /provider response was not valid JSON/,
    );
  });

  test("exit code 3 distinguishes credential failure from usage error", async () => {
    mode = "missing";
    stubFetch(okResponse());
    const { main } = await import("../bin/exa.mjs");
    const out = [];
    const realLog = console.log;
    console.log = (s) => out.push(s);
    const code = await main(["search", "hyprland"]);
    console.log = realLog;
    expect(code).toBe(3);
    expect(JSON.parse(out[0]).error).toMatch(/credential: missing access_token/);
  });

  test("usage error exits 2 without touching the network", async () => {
    const { main } = await import("../bin/exa.mjs");
    const out = [];
    const realLog = console.log;
    console.log = (s) => out.push(s);
    const code = await main(["search"]);
    console.log = realLog;
    expect(code).toBe(2);
    expect(JSON.parse(out[0]).error).toBe("query required");
  });
});
