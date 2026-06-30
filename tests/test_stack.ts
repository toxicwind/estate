#!/usr/bin/env bun
// Sovereign Stack — Bun-native health tests

const BASE = "http://127.0.0.1";

type Service = [number, string[]] | number;

const SERVICES: Record<string, Service> = {
  "llama-server": [25001, ["/health", "/v1/models"]],
  nfcot: [25003, ["/health", "/v1/models"]],
  openfang: [25004, ["/health"]],
  "rust-web": [25005, ["/health"]],
  "hf-downloader": [25020, ["/health"]],
  "llama-herder": [25021, ["/health"]],
  watchdog: [25022, ["/health"]],
  overlord: [25023, ["/health"]],
  landing: [25000, ["/", "/health"]],
  prometheus: [25030, ["/-/healthy", "/-/ready"]],
  "caddy-admin": [25031, ["/config/"]],
};

const INFRA: Record<string, number> = {
  postgres: 5432,
  redis: 6379,
  nats: 4222,
};

const green = (s: string) => `\x1b[92m${s}\x1b[0m`;
const red = (s: string) => `\x1b[91m${s}\x1b[0m`;
const yellow = (s: string) => `\x1b[93m${s}\x1b[0m`;

async function checkHttp(name: string, port: number, paths: string[]) {
  for (const path of paths) {
    try {
      const res = await fetch(`${BASE}:${port}${path}`, {
        signal: AbortSignal.timeout(2000),
      });
      if (res.status < 500) return [true, `${res.status} ${path}`] as const;
    } catch {}
  }
  return [false, `no response`] as const;
}

async function checkTcp(name: string, port: number) {
  try {
    const socket = await Bun.connect({
      hostname: "127.0.0.1",
      port,
      socket: { data: () => {} },
    });
    socket.end();
    return [true, "open"] as const;
  } catch (e) {
    return [false, "closed"] as const;
  }
}

async function testOne(name: string, spec: Service) {
  const [ok, msg] = Array.isArray(spec)
    ? await checkHttp(name, spec[0], spec[1])
    : await checkTcp(name, spec);

  const port = Array.isArray(spec) ? spec[0] : spec;
  const status = ok ? green("✓") : red("✗");
  console.log(
    `${status} ${name.padEnd(15)} :${String(port).padEnd(5)} → ${msg}`,
  );
  return ok;
}

console.log(`🚀 Sovereign Stack Test — ${new Date().toLocaleTimeString()}`);
console.log("-".repeat(55));

const all = { ...SERVICES, ...INFRA };
const results = await Promise.all(
  Object.entries(all).map(([n, s]) => testOne(n, s)),
);

console.log("-".repeat(55));
const passed = results.filter(Boolean).length;
if (passed === results.length) {
  console.log(green(`All ${passed} services healthy`));
  process.exit(0);
} else {
  console.log(
    yellow(`${passed}/${results.length} up — ${results.length - passed} down`),
  );
  console.log("\nTip: run `devenv up --detach` then `sovereign-logs`");
  process.exit(1);
}
