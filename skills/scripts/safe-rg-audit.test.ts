import { test, expect } from "bun:test";
import { safeSearch } from "./safe-rg-audit.ts";

test("safeSearch ignores log files and session directories", () => {
  const result = safeSearch({
    pattern: "api\\.nvidia\\.com",
    paths: ["/home/toxic/.tau"],
    timeoutMs: 4000,
  });

  // Verify it never touches active session log files
  expect(result.stdout).not.toContain(".bash.log");
  expect(result.stdout).not.toContain(".jsonl");
  expect(result.exitCode).toBeDefined();
});

test("safeSearch handles sub-second fast exits", () => {
  const start = performance.now();
  safeSearch({
    pattern: "SOMETHING_THAT_DOES_NOT_EXIST_XYZ123",
    paths: ["/home/toxic/.config/opencode"],
    timeoutMs: 2000,
  });
  const duration = performance.now() - start;
  expect(duration).toBeLessThan(1500);
});
