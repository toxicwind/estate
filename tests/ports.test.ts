/**
 * ports.ts unit tests — covers loadSovereignPorts, requireEnv, requirePort,
 * localUrl edge cases.
 */
import { describe, test, expect, beforeEach, afterEach } from "bun:test";
import { homedir } from "node:os";
import { join } from "node:path";

// Save original env
const origEnv: Record<string, string | undefined> = {};

beforeEach(() => {
  // Save relevant env vars
  for (const k of ["SOVEREIGN_ROOT", "LLAMA_SWAP_PORT", "SOME_PORT"]) {
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

// Import fresh each time — the module caches loadSovereignPorts internally,
// but we set SOVEREIGN_ROOT so the paths resolve predictably.
process.env.SOVEREIGN_ROOT = join(homedir(), "sovereign");

import {
  loadSovereignPorts,
  requireEnv,
  requirePort,
  localUrl,
} from "../src/lib/ports.ts";

describe("ports.ts", () => {
  test("loadSovereignPorts is idempotent (line 31-35)", () => {
    loadSovereignPorts();
    loadSovereignPorts(); // no throw
  });

  test("requireEnv throws for missing key", () => {
    delete process.env["NONEXISTENT_KEY_12345"];
    expect(() => requireEnv("NONEXISTENT_KEY_12345")).toThrow(
      "NONEXISTENT_KEY_12345 required",
    );
  });

  test("requireEnv returns existing env value (line 39)", () => {
    process.env["TEST_PORT_KEY"] = "25100";
    const v = requireEnv("TEST_PORT_KEY");
    expect(v).toBe("25100");
    delete process.env["TEST_PORT_KEY"];
  });

  test("requireEnv throws for empty string (line 41)", () => {
    process.env["EMPTY_KEY"] = "";
    expect(() => requireEnv("EMPTY_KEY")).toThrow("EMPTY_KEY required");
    delete process.env["EMPTY_KEY"];
  });

  test("requirePort returns valid number (line 48-53)", () => {
    process.env["LLAMA_SWAP_PORT"] = "25100";
    const port = requirePort("LLAMA_SWAP_PORT");
    expect(port).toBe(25100);
    expect(typeof port).toBe("number");
  });

  test("requirePort throws for non-numeric (line 50)", () => {
    process.env["LLAMA_SWAP_PORT"] = "not-a-number";
    expect(() => requirePort("LLAMA_SWAP_PORT")).toThrow("valid TCP port");
  });

  test("requirePort throws for zero (line 50)", () => {
    process.env["LLAMA_SWAP_PORT"] = "0";
    expect(() => requirePort("LLAMA_SWAP_PORT")).toThrow("valid TCP port");
  });

  test("requirePort throws for >65535 (line 50)", () => {
    process.env["LLAMA_SWAP_PORT"] = "99999";
    expect(() => requirePort("LLAMA_SWAP_PORT")).toThrow("valid TCP port");
  });

  test("requirePort throws for negative (line 50)", () => {
    process.env["LLAMA_SWAP_PORT"] = "-1";
    expect(() => requirePort("LLAMA_SWAP_PORT")).toThrow("valid TCP port");
  });

  test("localUrl builds correct URL (line 57-61)", () => {
    process.env["LLAMA_SWAP_PORT"] = "25100";
    const url = localUrl("LLAMA_SWAP_PORT");
    expect(url).toBe("http://127.0.0.1:25100");
  });

  test("localUrl appends path with leading slash", () => {
    process.env["LLAMA_SWAP_PORT"] = "25100";
    const url = localUrl("LLAMA_SWAP_PORT", "/v1/models");
    expect(url).toBe("http://127.0.0.1:25100/v1/models");
  });

  test("localUrl adds slash before non-empty path", () => {
    process.env["LLAMA_SWAP_PORT"] = "25100";
    const url = localUrl("LLAMA_SWAP_PORT", "v1/models");
    expect(url).toBe("http://127.0.0.1:25100/v1/models");
  });

  test("localUrl with empty path", () => {
    process.env["LLAMA_SWAP_PORT"] = "25100";
    const url = localUrl("LLAMA_SWAP_PORT", "");
    expect(url).toBe("http://127.0.0.1:25100");
  });
});
