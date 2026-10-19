// capout.test.ts — regression tests for the output-persistence fix.
// Truncated exec output must persist COMPLETE output to a durable file;
// under-cap output passes through untouched.
import { describe, expect, test, beforeAll } from "bun:test";
import { existsSync, readFileSync, rmSync } from "node:fs";
import { capOut } from "../src/index.ts";

const TEST_DIR = "/tmp/awrawr-capout-test";

beforeAll(() => {
  rmSync(TEST_DIR, { recursive: true, force: true });
  process.env.AWR_MCP_OUTPUT_DIR = TEST_DIR;
});

describe("capOut", () => {
  test("under-cap output passes through, not truncated", () => {
    const r = capOut("[exit=0] ", "hello");
    expect(r.truncated).toBe(false);
    expect(r.text).toBe("[exit=0] hello");
  });

  test("empty output renders the (no output) marker", () => {
    const r = capOut("[exit=0] ", "");
    expect(r.truncated).toBe(false);
    expect(r.text).toBe("[exit=0] (no output)");
  });

  test("over-cap output is truncated in-band and fully persisted", () => {
    const full = "x".repeat(25_000) + "TAIL-MARKER";
    const r = capOut("[exit=0] ", full);
    expect(r.truncated).toBe(true);
    expect(r.text).toContain("[TRUNCATED 25011 chars total");
    const m = r.text.match(/full output saved to (\S+)\]/);
    expect(m).not.toBeNull();
    const saved = m![1];
    expect(existsSync(saved)).toBe(true);
    // The persisted file holds the COMPLETE output, byte-exact.
    expect(readFileSync(saved, "utf8")).toBe(full);
  });
});
