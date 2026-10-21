/**
 * smithers-gateway-lib.test.ts — unit tests for the estate Smithers Gateway
 * launcher's pure core (smithers-gateway-lib.ts). Run: `bun test`.
 */
import { expect, test, describe } from "bun:test";
import { mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import {
  loadEnvFileInto,
  resolvePort,
  buildGatewayArgv,
  HOST,
  IDLE_TIMEOUT,
  KEYRING_SPECS,
  SECRET_VAR_NAMES,
} from "./smithers-gateway-lib.ts";

describe("loadEnvFileInto", () => {
  test("parses plain KEY=VAL, strips quotes, ignores comments", () => {
    const dir = mkdtempSync(join(tmpdir(), "smithers-lib-"));
    const f = join(dir, "x.env");
    writeFileSync(
      f,
      [
        "",
        "# a comment",
        "A=b",
        `C="with space"`,
        "D='single'",
        "  E =  padded  ", // tolerate surrounding whitespace
        "",
      ].join("\n"),
    );
    const env: Record<string, string | undefined> = {};
    loadEnvFileInto(env, f);
    expect(env.A).toBe("b");
    expect(env.C).toBe("with space");
    expect(env.D).toBe("single");
    expect(env.E).toBe("padded");
    rmSync(dir, { recursive: true, force: true });
  });

  test("parses export-prefixed lines", () => {
    const dir = mkdtempSync(join(tmpdir(), "smithers-lib-"));
    const f = join(dir, "y.env");
    writeFileSync(f, "export FOO=bar\nexport BAZ=qux\n");
    const env: Record<string, string | undefined> = {};
    loadEnvFileInto(env, f);
    expect(env.FOO).toBe("bar");
    expect(env.BAZ).toBe("qux");
    rmSync(dir, { recursive: true, force: true });
  });

  test("never overrides an already-set value", () => {
    const dir = mkdtempSync(join(tmpdir(), "smithers-lib-"));
    const f = join(dir, "z.env");
    writeFileSync(f, "SSOT=file\n");
    const env: Record<string, string | undefined> = { SSOT: "existing" };
    loadEnvFileInto(env, f);
    expect(env.SSOT).toBe("existing");
    rmSync(dir, { recursive: true, force: true });
  });

  test("missing file is a no-op", () => {
    const env: Record<string, string | undefined> = {};
    loadEnvFileInto(env, "/definitely/not/a/real/path-xyz.env");
    expect(env).toStrictEqual({});
  });
});

describe("resolvePort", () => {
  test("reads the SSOT port from env", () => {
    expect(resolvePort({ SMITHERS_GATEWAY_PORT: "25280" })).toBe(25280);
  });
  test("falls back to the default when unset", () => {
    expect(resolvePort({})).toBe(25280);
  });
  test("rejects junk and falls back", () => {
    expect(resolvePort({ SMITHERS_GATEWAY_PORT: "not-a-number" })).toBe(25280);
    expect(resolvePort({ SMITHERS_GATEWAY_PORT: "-1" })).toBe(25280);
    expect(resolvePort({ SMITHERS_GATEWAY_PORT: "70000" })).toBe(25280);
  });
});

describe("buildGatewayArgv", () => {
  test("binds loopback on the resolved port, never idle-exits", () => {
    const argv = buildGatewayArgv(25280);
    expect(argv).toEqual([
      "bunx",
      "smthrs",
      "gateway",
      "--host",
      HOST,
      "--port",
      "25280",
      "--idle-timeout",
      IDLE_TIMEOUT,
    ]);
  });
  test("does not touch the default 7331 (estate 25xxx fleet SSOT)", () => {
    expect(HOST).toBe("127.0.0.1");
    expect(IDLE_TIMEOUT).toBe("0");
    expect(buildGatewayArgv(25280)).not.toContain("7331");
  });
});

describe("KEYRING_SPECS", () => {
  test("covers the retireed .sh spec_of() mappings", () => {
    expect(KEYRING_SPECS.HODOS_API_KEY).toEqual({ service: "hodos" });
    expect(KEYRING_SPECS.NIM_PROXY_API_KEY).toEqual({
      service: "nim",
      provider: "nvidia",
    });
    expect(KEYRING_SPECS.NVIDIA_API_KEY).toEqual({
      service: "nim",
      provider: "nvidia",
    });
    expect(KEYRING_SPECS.ANTHROPIC_API_KEY).toEqual({ service: "anthropic" });
    expect(KEYRING_SPECS.OPENROUTER_API_KEY).toEqual({ service: "openrouter" });
  });
  test("exposes the secret var names", () => {
    expect(SECRET_VAR_NAMES).toContain("HODOS_API_KEY");
    expect(SECRET_VAR_NAMES).toContain("ANTHROPIC_API_KEY");
  });
});
