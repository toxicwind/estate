/**
 * ports.ts unit tests — covers loadEstatePorts, requireEnv, requirePort,
 * localUrl edge cases.
 */
import { afterEach, beforeEach, describe, expect, test } from "bun:test";
import { join } from "node:path";

// Save original env
const origEnv: Record<string, string | undefined> = {};

beforeEach(() => {
  // Save relevant env vars
  for (const k of ["ESTATE_ROOT", "HERD_PORT", "SOME_PORT"]) {
    origEnv[k] = process.env[k];
  }
});

afterEach(() => {
  // Restore env
  for (const k of Object.keys(origEnv)) {
    if (origEnv[k] !== undefined) process.env[k] = origEnv[k];
    else delete process.env[k];
  }
});

// Import fresh each time — the module caches loadEstatePorts internally,
// but we set ESTATE_ROOT so the paths resolve predictably. Derive the estate
// root from THIS file's real location (the checked-out repo) instead of
// hardcoding ${HOME}/estate — the latter breaks on GitHub Actions runners
// where the checkout lives at /home/runner/work/<repo>/<repo>.
process.env.ESTATE_ROOT = join(import.meta.dir, "..");

import {
  loadEstatePorts,
  localUrl,
  requireEnv,
  requirePort,
} from "../src/lib/ports.ts";

describe("ports.ts", () => {
  test("loadEstatePorts is idempotent (line 31-35)", () => {
    loadEstatePorts();
    loadEstatePorts(); // no throw
  });

  test("requireEnv throws for missing key", () => {
    delete process.env.NONEXISTENT_KEY_12345;
    expect(() => requireEnv("NONEXISTENT_KEY_12345")).toThrow(
      "NONEXISTENT_KEY_12345 required",
    );
  });

  test("requireEnv returns existing env value (line 39)", () => {
    process.env.TEST_PORT_KEY = "25100";
    const v = requireEnv("TEST_PORT_KEY");
    expect(v).toBe("25100");
    delete process.env.TEST_PORT_KEY;
  });

  test("requireEnv throws for empty string (line 41)", () => {
    process.env.EMPTY_KEY = "";
    expect(() => requireEnv("EMPTY_KEY")).toThrow("EMPTY_KEY required");
    delete process.env.EMPTY_KEY;
  });

  test("requirePort returns valid number (line 48-53)", () => {
    process.env.HERD_PORT = "25100";
    const port = requirePort("HERD_PORT");
    expect(port).toBe(25100);
    expect(typeof port).toBe("number");
  });

  test("requirePort throws for non-numeric (line 50)", () => {
    process.env.HERD_PORT = "not-a-number";
    expect(() => requirePort("HERD_PORT")).toThrow("valid TCP port");
  });

  test("requirePort throws for zero (line 50)", () => {
    process.env.HERD_PORT = "0";
    expect(() => requirePort("HERD_PORT")).toThrow("valid TCP port");
  });

  test("requirePort throws for >65535 (line 50)", () => {
    process.env.HERD_PORT = "99999";
    expect(() => requirePort("HERD_PORT")).toThrow("valid TCP port");
  });

  test("requirePort throws for negative (line 50)", () => {
    process.env.HERD_PORT = "-1";
    expect(() => requirePort("HERD_PORT")).toThrow("valid TCP port");
  });

  test("localUrl builds correct URL (line 57-61)", () => {
    process.env.HERD_PORT = "25100";
    const url = localUrl("HERD_PORT");
    expect(url).toBe("http://127.0.0.1:25100");
  });

  test("localUrl appends path with leading slash", () => {
    process.env.HERD_PORT = "25100";
    const url = localUrl("HERD_PORT", "/v1/models");
    expect(url).toBe("http://127.0.0.1:25100/v1/models");
  });

  test("localUrl adds slash before non-empty path", () => {
    process.env.HERD_PORT = "25100";
    const url = localUrl("HERD_PORT", "v1/models");
    expect(url).toBe("http://127.0.0.1:25100/v1/models");
  });

  test("localUrl with empty path", () => {
    process.env.HERD_PORT = "25100";
    const url = localUrl("HERD_PORT", "");
    expect(url).toBe("http://127.0.0.1:25100");
  });
});
