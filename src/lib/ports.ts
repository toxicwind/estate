/**
 * Port SSOT loader for Bun services.
 * Values live only in config/ports.env (and optional .env.local overrides).
 * Never invent numeric ports in application code.
 */
import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { resolve } from "node:path";

const SOV =
  process.env.SOVEREIGN_ROOT ||
  resolve(homedir(), "sovereign");

function loadEnvFile(path: string): void {
  if (!existsSync(path)) return;
  for (let line of readFileSync(path, "utf8").split("\n")) {
    line = line.trim();
    if (!line || line.startsWith("#")) continue;
    if (line.startsWith("export ")) line = line.slice(7);
    const eq = line.indexOf("=");
    if (eq < 1) continue;
    const k = line.slice(0, eq).trim();
    let v = line.slice(eq + 1).trim().replace(/^['"]|['"]$/g, "");
    if (k && v !== undefined && process.env[k] === undefined) {
      process.env[k] = v;
    }
  }
}

/** Idempotent: load ports.env then .env.local into process.env */
export function loadSovereignPorts(): void {
  loadEnvFile(resolve(SOV, "config/ports.env"));
  loadEnvFile(resolve(SOV, ".env.local"));
  loadEnvFile(resolve(homedir(), ".secrets"));
}

export function requireEnv(name: string): string {
  loadSovereignPorts();
  const v = process.env[name];
  if (v === undefined || v === "") {
    throw new Error(
      `${name} required — set in ${SOV}/config/ports.env (25xxx SSOT)`,
    );
  }
  return v;
}

export function requirePort(name: string): number {
  const n = Number(requireEnv(name));
  if (!Number.isFinite(n) || n < 1 || n > 65535) {
    throw new Error(`${name} must be a valid TCP port, got ${process.env[name]}`);
  }
  return n;
}

/** http://127.0.0.1:${PORT}${path} */
export function localUrl(portEnv: string, path = ""): string {
  const port = requireEnv(portEnv);
  const p = path.startsWith("/") ? path : path ? `/${path}` : "";
  return `http://127.0.0.1:${port}${p}`;
}
