#!/usr/bin/env bun
/**
 * OpenFang entry — secrets, daemon on backend port, mesh-front on public OPENFANG_PORT.
 */
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { requirePort, loadSovereignPorts } from "../lib/ports.ts";

loadSovereignPorts();
const HOME = process.env.HOME || "/home/toxic";
const PUBLIC = requirePort("OPENFANG_PORT");
const BACKEND = Number(process.env.OPENFANG_BACKEND_PORT || "26103");
const BIN = process.env.OPENFANG_BIN || `${HOME}/.openfang/bin/openfang`;
const SOV = process.env.SOVEREIGN_ROOT || resolve(HOME, "sovereign");

function loadSecretsFile(path: string) {
  if (!existsSync(path)) return;
  for (const line of readFileSync(path, "utf8").split("\n")) {
    if (!line || line.startsWith("#") || !line.includes("=")) continue;
    const eq = line.indexOf("=");
    const key = line.slice(0, eq).trim();
    if (!key || process.env[key]) continue;
    let val = line.slice(eq + 1).trim();
    if (
      (val.startsWith('"') && val.endsWith('"')) ||
      (val.startsWith("'") && val.endsWith("'"))
    ) {
      val = val.slice(1, -1);
    }
    process.env[key] = val;
  }
}

loadSecretsFile(resolve(HOME, ".secrets"));
loadSecretsFile(resolve(HOME, ".openfang/secrets.env"));

// Force OpenFang binary onto backend port (config.toml + daemon.json are SSOT for listen)
function pinOpenfangBackend(port: number) {
  const conf = resolve(HOME, ".openfang/config.toml");
  if (existsSync(conf)) {
    let t = readFileSync(conf, "utf8");
    t = t.replace(
      /api_listen\s*=\s*"[^"]*"/,
      `api_listen = "127.0.0.1:${port}"`,
    );
    if (!t.includes("api_listen")) {
      t = `api_listen = "127.0.0.1:${port}"\n` + t;
    }
    Bun.write(conf, t);
  }
  const daemon = resolve(HOME, ".openfang/daemon.json");
  if (existsSync(daemon)) {
    try {
      const j = JSON.parse(readFileSync(daemon, "utf8"));
      j.listen_addr = `127.0.0.1:${port}`;
      Bun.write(daemon, JSON.stringify(j, null, 2));
    } catch {
      /* ignore */
    }
  }
}

pinOpenfangBackend(BACKEND);

const env = {
  ...process.env,
  HOST: "127.0.0.1",
  BIND: "127.0.0.1",
  OPENFANG_PORT: String(BACKEND),
};

console.log(`[OpenFang] backend :${BACKEND} mesh-front :${PUBLIC}`);

// stop any prior
Bun.spawnSync({
  cmd: [BIN, "stop"],
  env,
  stdout: "ignore",
  stderr: "ignore",
});

const start = Bun.spawn({
  cmd: [BIN, "start", "--yolo"],
  env,
  stdout: "inherit",
  stderr: "inherit",
});

for (let i = 0; i < 40; i++) {
  try {
    if ((await fetch(`http://127.0.0.1:${BACKEND}/api/health`)).ok) break;
  } catch {
    /* retry */
  }
  await Bun.sleep(250);
}

const front = Bun.spawn({
  cmd: [
    "/home/toxic/.bun/bin/bun",
    "run",
    resolve(SOV, "src/services/mesh-front.ts"),
    "--service",
    "openfang",
    "--listen",
    `0.0.0.0:${PUBLIC}`,
    "--backend",
    `127.0.0.1:${BACKEND}`,
  ],
  stdout: "inherit",
  stderr: "inherit",
});

const stop = () => {
  front.kill();
  Bun.spawnSync({
    cmd: [BIN, "stop"],
    env,
    stdout: "ignore",
    stderr: "ignore",
  });
  start.kill();
  process.exit(0);
};
process.on("SIGTERM", stop);
process.on("SIGINT", stop);

const code = await front.exited;
process.exit(code ?? 0);
