#!/usr/bin/env bun
/**
 * OpenFang process-compose entry — load secrets then start daemon.
 * Port SSOT: OPENFANG_PORT from mise (25103). Never vLLM.
 */
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

const HOME = process.env.HOME || "/home/toxic";
const PORT = parseInt(process.env.OPENFANG_PORT || "25103", 10);
const BIN = process.env.OPENFANG_BIN || `${HOME}/.openfang/bin/openfang`;

/** Load KEY=VAL from a secrets file into env if not already set. */
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

const env = {
  ...process.env,
  HOST: "0.0.0.0",
  BIND: "0.0.0.0",
  OPENFANG_PORT: String(PORT),
};

// Sub-second discipline: short health waits (500ms × 20 = 10s max)
const HEALTH_TRIES = 20;
const HEALTH_MS = 500;

console.log(`[OpenFang] start --yolo on 0.0.0.0:${PORT}`);
console.log(
  `[OpenFang] discord_token=${process.env.DISCORD_BOT_TOKEN ? "set" : "MISSING"} telegram_token=${process.env.TELEGRAM_BOT_TOKEN ? "set" : "MISSING"}`,
);

const stop = () => {
  Bun.spawnSync({ cmd: [BIN, "stop"], env, stdout: "ignore", stderr: "ignore" });
  process.exit(0);
};
process.on("SIGTERM", stop);
process.on("SIGINT", stop);

const r = Bun.spawnSync({
  cmd: [BIN, "start", "--yolo"],
  env,
  stdout: "inherit",
  stderr: "inherit",
});
if (r.exitCode !== 0) process.exit(r.exitCode ?? 1);

for (let i = 0; i < HEALTH_TRIES; i++) {
  try {
    if ((await fetch(`http://127.0.0.1:${PORT}/api/health`)).ok) break;
  } catch {
    /* retry */
  }
  await Bun.sleep(HEALTH_MS);
}

console.log(`[OpenFang] daemon up, holding foreground for process-compose`);
await new Promise(() => {});
