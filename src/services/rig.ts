#!/usr/bin/env bun
/**
 * Rig public front — mesh-front on RIG_PORT proxying the single
 * Rig kernel on RIG_KERNEL_PORT.
 *
 * Canonical map (2026-09-21 full audit):
 *   :25196 (RIG_KERNEL_PORT) — the ONE kernel (pitchfork daemons.rig,
 *            ops/rig-run.sh). Serves the dashboard UI + /v1 (OpenAI-compat)
 *            + /api. Owns ~/.rig (config, SQLite DB, triggers).
 *   :25103 (RIG_PORT)        — THIS service: mesh-front reverse proxy in
 *            front of the kernel (adds /mesh/* GHAS features on the public port).
 *   :25203 — RETIRED 2026-09-21. It  a DUPLICATE kernel sharing the same
 *            SQLite DB (double-writer hazard), split-brain heartbeat warnings,
 *            and flapped the CLI's API target between instances.
 *   :4200  — RETIRED (legacy pre-migration port; config moved to
 *            config/deprecated/rig-4200.toml).
 *
 * This service NEVER spawns the rig binary and NEVER mutates
 * ~/.rig/config.toml or daemon.json — the kernel owns its own lifecycle
 * and config. See ops/rig-run.sh.
 */
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { loadEstatePorts, requirePort } from "../lib/ports.ts";

loadEstatePorts();
const HOME = process.env.HOME || "/home/toxic";
const PUBLIC = requirePort("RIG_PORT");
const KERNEL = requirePort("RIG_KERNEL_PORT");
const SOV = process.env.ESTATE_ROOT || resolve(HOME, "estate");

function loadSecretsFile(path: string) {
  if (!existsSync(path)) return;
  for (const line of readFileSync(path, "utf8").split("\n")) {
    if (!line || line.startsWith("#") || !line.includes("=")) continue;
    const eq = line.indexOf("=");
    const key = line.slice(0, eq).trim().replace(/^export\s+/, "");
    // Canonical file wins: overwrite any value inherited from the
    // supervisor environment (stale/rotated keys must not survive).
    if (!key) continue;
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

// No real Anthropic key exists - Anthropic-compat goes through nim-proxy.
// Drop any stale/bogus key inherited from the supervisor environment
// before the canonical file loads (it stays the source of truth).
delete process.env.ANTHROPIC_API_KEY;

loadSecretsFile(resolve(HOME, ".secrets"));
loadSecretsFile(resolve(HOME, ".rig/secrets.env"));

console.log(`[rig-front] kernel :${KERNEL} mesh-front :${PUBLIC}`);

// Bounded boot gate (one-shot, not a polling daemon): wait for the kernel's
// real API before exposing the proxy. If the kernel never comes up we still
// start the listener so the port is held and the backend 502s loudly instead
// of the port going dark.
const deadline = Date.now() + 60_000;
let kernelUp = false;
while (Date.now() < deadline) {
  try {
    const r = await fetch(`http://127.0.0.1:${KERNEL}/api/health`, {
      signal: AbortSignal.timeout(3000),
    });
    if (r.ok) {
      kernelUp = true;
      break;
    }
  } catch {
    /* kernel not up yet */
  }
  await Bun.sleep(1000);
}
if (!kernelUp) {
  console.error(
    `[rig-front] kernel :${KERNEL} not healthy after 60s — starting proxy anyway (backend will 502)`
  );
}

const front = Bun.spawn({
  cmd: [
    "/home/toxic/.bun/bin/bun",
    "run",
    resolve(SOV, "src/services/mesh-front.ts"),
    "--service",
    "rig",
    // 2026-10-15: bind loopback, not 0.0.0.0 — recon front is internal-only,
    // the tailnet is reached via estate-chat; remove the nftables dependency.
    "--listen",
    `127.0.0.1:${PUBLIC}`,
    "--backend",
    `127.0.0.1:${KERNEL}`,
  ],
  stdout: "inherit",
  stderr: "inherit",
});

const stop = () => {
  front.kill();
  process.exit(0);
};
process.on("SIGTERM", stop);
process.on("SIGINT", stop);

const code = await front.exited;
process.exit(code ?? 0);
