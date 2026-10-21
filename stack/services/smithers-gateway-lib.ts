/**
 * smithers-gateway-lib.ts — pure, testable core of the estate Smithers Gateway
 * launcher. Split out of smithers-gateway.ts so the env-file parsing, SSOT port
 * resolution, and keyring-spec bookkeeping are unit-testable without spawning a
 * real gateway. No side effects at import time.
 */
import { readFileSync, existsSync } from "node:fs";

/** Load a KEY=VAL / export KEY=VAL file into `env` (only sets keys already unset). */
export function loadEnvFileInto(
  env: Record<string, string | undefined>,
  path: string,
): void {
  if (!existsSync(path)) return;
  for (const raw of readFileSync(path, "utf8").split("\n")) {
    const line = raw.trim();
    if (!line || line.startsWith("#")) continue;
    const body = line.startsWith("export ") ? line.slice(7).trim() : line;
    const eq = body.indexOf("=");
    if (eq < 1) continue;
    const key = body.slice(0, eq).trim();
    let value = body.slice(eq + 1).trim();
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    if (key && env[key] === undefined) env[key] = value;
  }
}

/** Resolve the gateway port from env, falling back to the estate SSOT default. */
export function resolvePort(env: Record<string, string | undefined>): number {
  const raw = env.SMITHERS_GATEWAY_PORT ?? "25280";
  const n = Number(raw);
  return Number.isInteger(n) && n > 0 && n < 65536 ? n : 25280;
}

/** The gateway is loopback-bound; tailscale fronts it for any network surface. */
export const HOST = "127.0.0.1";
/** Estate singleton: never idle-exits while supervised by pitchfork. */
export const IDLE_TIMEOUT = "0";

/** VAR -> keyring attribute spec. Mirrors the retired .sh spec_of() mappings. */
export const KEYRING_SPECS: Record<string, Record<string, string>> = {
  HODOS_API_KEY: { service: "hodos" },
  NIM_PROXY_API_KEY: { service: "nim", provider: "nvidia" },
  NVIDIA_API_KEY: { service: "nim", provider: "nvidia" },
  ANTHROPIC_API_KEY: { service: "anthropic" },
  OPENROUTER_API_KEY: { service: "openrouter" },
};

/** Build the argv for `bunx smthrs gateway` given a resolved port. */
export function buildGatewayArgv(port: number, host = HOST): string[] {
  return [
    "bunx",
    "smthrs",
    "gateway",
    "--host",
    host,
    "--port",
    String(port),
    "--idle-timeout",
    IDLE_TIMEOUT,
  ];
}

/** Keys known to carry secrets; used to reason about env without printing them. */
export const SECRET_VAR_NAMES = Object.keys(KEYRING_SPECS);
