import { describe, test, expect } from "bun:test";
import {
  llamaSwapHealth,
  llamaSwapModels,
  llamaSwapChat,
  vscodeSettingsCheck,
  copilotByokE2e,
} from "../src/mcp/llama_swap.ts";

describe("llama-swap live front door :25100", () => {
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
    expect((c as { choices_count?: number }).choices_count).toBeGreaterThanOrEqual(1);
  });

  test("vscode settings plugin path", () => {
    const s = vscodeSettingsCheck();
    expect(s.ok).toBe(true);
    expect(s.path).toBe("oaicopilot_plugin");
    expect(s.baseUrl_is_25100).toBe(true);
  });

  test("copilot byok e2e", async () => {
    const r = await copilotByokE2e({ model: "beellama/qwen-flash-64k" });
    expect(r.ok).toBe(true);
    expect(r.chat.ok).toBe(true);
  });
});
