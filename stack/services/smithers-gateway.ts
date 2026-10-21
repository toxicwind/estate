#!/usr/bin/env bun
/**
 * smithers-gateway.ts — real TypeScript runner for the estate Smithers Gateway,
 * replacing the fragile `smithers-gateway.sh` bash shim (gatehouse-serve.ts
 * precedent). Pure TypeScript; no bash indirection.
 *
 * Responsibilities, in order:
 *   1. Load SSOT ports from config/ports.env onto process.env (yote.ts pattern).
 *   2. Load the ~/.secrets vault as the silent fallback layer (never the source
 *      of truth).
 *   3. Overlay keyring secrets via the secretsmith Bun drop-in (ranch/secretsmith
 *      /bun, `get()` == the .sh's `spec_of` probe: inject ONLY vars that have an
 *      exact-one keyring match; everything else falls through to the vault that
 *      was already sourced).
 *   4. Spawn `bunx smthrs gateway` bound to the SSOT port on loopback, with the
 *      merged env. Every smithers-spawned agent inherits this env, so the
 *      model/routing keys MUST be resolvable here at gateway boot.
 *
 * The pure/env-free core (parsing, port resolution, argv building, keyring spec
 * table) lives in smithers-gateway-lib.ts and is unit-tested there.
 *
 * Secrets travel in child-process env only — nothing is printed, logged, or
 * written. `estate` cwd is passed so the gateway picks the estate workspace.
 */
import { join } from "node:path";
import { homedir } from "node:os";
import { fileURLToPath } from "node:url";

// keysmith Bun drop-in — keyring-first secret resolution. Relative import so it
// resolves regardless of node_modules linkage. From stack/services/ the estate
// ranch/ tree is TWO levels up.
import { get } from "../../ranch/secretsmith/bun/src/index.ts";
import {
  loadEnvFileInto,
  resolvePort,
  buildGatewayArgv,
  HOST,
  KEYRING_SPECS,
} from "./smithers-gateway-lib.ts";

const here = fileURLToPath(import.meta.url);
const ESTATE = join(here, "..", ".."); // stack/services -> estate root
const PORTS_ENV = join(ESTATE, "config", "ports.env");
const VaultFile = join(homedir(), ".secrets");

// 1) SSOT ports + 2) vault fallback (silent; never overrides an existing value).
loadEnvFileInto(process.env as Record<string, string | undefined>, PORTS_ENV);
loadEnvFileInto(process.env as Record<string, string | undefined>, VaultFile);

const PORT = resolvePort(process.env as Record<string, string | undefined>);

// 3) keyring overlay — inject ONLY vars with an exact-one keyring match so the
//    already-sourced vault fallback stands otherwise (mirrors .sh spec_of).
const secrets: Record<string, string> = {};
for (const [varName, attrs] of Object.entries(KEYRING_SPECS)) {
  if (process.env[varName]) continue; // vault/shell already provided it
  try {
    const item = await get(attrs); // exact-one-or-null
    if (item?.secret) secrets[varName] = item.secret;
  } catch {
    // keyring unavailable (no DBus, locked, etc.) -> let the vault fallback stand
  }
}

// 4) spawn the gateway with the merged env and mirror its lifecycle.
const child = Bun.spawn(buildGatewayArgv(PORT, HOST), {
  cwd: ESTATE,
  env: { ...process.env, ...secrets },
  stdout: "inherit",
  stderr: "inherit",
  stdin: "inherit",
});

process.on("SIGTERM", () => child.kill("SIGTERM"));
process.on("SIGINT", () => child.kill("SIGINT"));
process.on("SIGHUP", () => child.kill("SIGHUP"));

const code = await child.exited;
process.exit(code ?? 1);
