// ripline tests — protocol classification + fallover ledger + transport framing.
// Run: bun test
import { describe, expect, test } from "bun:test";
import { classifyDaemonError, isPreDispatchError } from "../src/protocol.ts";
import { falloverCount } from "../src/fallover.ts";

describe("protocol: no-double-exec contract", () => {
  test("pre-dispatch daemon errors are safe to re-dispatch", () => {
    for (const m of [
      "bridge not connected: ws handshake failed",
      "send failed: reconnecting",
      "daemon unavailable (no socket)",
      "ws send to daemon failed (pre-dispatch)",
    ]) {
      expect(isPreDispatchError(m)).toBe(true);
    }
  });
  test("post-dispatch daemon errors must NOT re-dispatch", () => {
    for (const m of [
      "command may have executed remotely, response timeout",
      "ws response timeout (no retry)",
      "post-dispatch failure: may have executed",
    ]) {
      const c = classifyDaemonError(m);
      expect(c.postDispatch).toBe(true);
      expect(c.preDispatch).toBe(false);
    }
  });
  test("empty/unknown messages default to pre-dispatch (fail-open to mainline)", () => {
    expect(isPreDispatchError("")).toBe(true);
  });
});

describe("fallover ledger", () => {
  test("ledger count reads without throwing when absent", () => {
    expect(typeof falloverCount()).toBe("number");
  });
});
