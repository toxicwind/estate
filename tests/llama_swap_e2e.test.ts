import { describe, test, expect } from "bun:test";
import {
  llamaSwapHealth,
  llamaSwapModels,
  llamaSwapChat,
} from "../src/mcp/llama_swap.ts";

// Skip integration tests if llama-swap is not running (top-level await)
let live = false;
try {
  const r = await llamaSwapHealth();
  live = r.http_status === 200;
} catch {
  live = false;
}

describe.skipIf(!live)("llama-swap live front door :25100", () => {
  test("health 200", async () => {
    const h = await llamaSwapHealth();
    expect(h.http_status).toBe(200);
  });

  test("models non-empty", async () => {
    const m = await llamaSwapModels();
    expect(m.http_status).toBe(200);
    expect((m as { count?: number }).count ?? 0).toBeGreaterThan(0);
  });

  test("chat choices >= 1", async () => {
    const c = await llamaSwapChat({
      model: "beellama/qwen-flash-64k",
      prompt: "Reply with exactly: OK",
      max_tokens: 16,
    });
    expect(c.ok).toBe(true);
    expect(
      (c as { choices_count?: number }).choices_count,
    ).toBeGreaterThanOrEqual(1);
  });
});
