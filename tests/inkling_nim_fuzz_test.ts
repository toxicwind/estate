#!/usr/bin/env bun
/**
 * inkling_nim_fuzz_test.ts — Systematic parameter fuzz test for NVIDIA NIM Inkling
 * Uses llama-swap :25100 (local router) via sovereign infrastructure
 * 
 * Tests ALL standard OpenAI parameters + NIM-specific extensions
 * Discovers what's actually supported vs rejected
 * 
 * Run: bun test tests/inkling_nim_fuzz_test.ts
 */

import { describe, test, expect, beforeAll, afterAll } from "bun:test";
import { llamaSwapHealth, llamaSwapModels, llamaSwapChat, llamaSwapChatStream, upstreamServers } from "../src/mcp/llama_swap.ts";

const INKLING_MODEL = "thinkingmachines/inkling";
const TEST_PROMPT = "Hi";
const RATE_LIMIT_DELAY_MS = 3000; // 20 RPM = 3s between requests
const TEST_TIMEOUT_MS = 60000; // 60s for slow tests

// Rate limiter
let lastRequestTime = 0;
async function rateLimit() {
  const now = Date.now();
  const elapsed = now - lastRequestTime;
  if (elapsed < RATE_LIMIT_DELAY_MS) {
    await new Promise(resolve => setTimeout(resolve, RATE_LIMIT_DELAY_MS - elapsed));
  }
  lastRequestTime = Date.now();
}

// Test result tracker
interface TestResult {
  name: string;
  category: string;
  success: boolean;
  status: number;
  elapsedMs: number;
  error?: string;
  supported: boolean; // true if param is accepted (200 or 429), false if rejected (400/500 with "unknown")
}

const results: TestResult[] = [];

async function runTest(name: string, category: string, payload: any, timeoutMs = TEST_TIMEOUT_MS): Promise<TestResult> {
  await rateLimit();
  const start = Date.now();
  try {
    const result = await Promise.race([
      llamaSwapChat({
        ...payload,
        model: INKLING_MODEL,
      }),
      new Promise<never>((_, reject) => 
        setTimeout(() => reject(new Error(`Test timeout after ${timeoutMs}ms`)), timeoutMs)
      )
    ]);
    const elapsed = Date.now() - start;
    
    // Determine if parameter is supported
    // 200 = success, 429 = rate limited (param accepted), 400/500 with "unknown" = rejected
    const errorStr = result.error ? JSON.stringify(result.error).toLowerCase() : "";
    const isRejected = (result.http_status === 400 || result.http_status === 500) && 
                       (errorStr.includes("unknown") || errorStr.includes("unexpected") || errorStr.includes("invalid parameter"));
    const isSupported = result.http_status === 200 || result.http_status === 429 || !isRejected;
    
    const testResult: TestResult = {
      name,
      category,
      success: result.ok === true,
      status: result.http_status,
      elapsedMs: elapsed,
      error: result.error ? JSON.stringify(result.error).slice(0, 200) : undefined,
      supported: isSupported,
    };
    
    results.push(testResult);
    return testResult;
  } catch (e) {
    const elapsed = Date.now() - start;
    const testResult: TestResult = {
      name,
      category,
      success: false,
      status: 0,
      elapsedMs: elapsed,
      error: String(e).slice(0, 200),
      supported: false,
    };
    results.push(testResult);
    return testResult;
  }
}

// ──────────────────────────────────────────────────────────────
// TEST SUITE
// ──────────────────────────────────────────────────────────────

describe("Inkling NIM Parameter Fuzz Test — Systematic Coverage", () => {
  let healthCheck: any;
  
  beforeAll(async () => {
    healthCheck = await llamaSwapHealth();
    console.log("[HEALTH]", healthCheck);
    if (healthCheck.http_status !== 200) {
      throw new Error("llama-swap health check failed");
    }
    
    const models = await llamaSwapModels();
    const inklingModels = (models as any).models?.filter((m: any) => 
      m.id.toLowerCase().includes("inkling")
    ) || [];
    console.log("[INKLING MODELS]", inklingModels.map((m: any) => m.id));
  }, 30000);

  // ══════════════════════════════════════════════════════════════
  // CATEGORY 1: MAX_TOKENS BOUNDARIES
  // ══════════════════════════════════════════════════════════════

  describe("max_tokens boundaries", () => {
    const testCases = [
      { name: "max_tokens_1", value: 1 },
      { name: "max_tokens_5", value: 5 },
      { name: "max_tokens_10", value: 10 },
      { name: "max_tokens_50", value: 50 },
      { name: "max_tokens_100", value: 100 },
      { name: "max_tokens_500", value: 500 },
      { name: "max_tokens_1k", value: 1024 },
      { name: "max_tokens_4k", value: 4096 },
      { name: "max_tokens_16k", value: 16384 },
      { name: "max_tokens_32k", value: 32768 },
      { name: "max_tokens_65k", value: 65536 },
    ];

    for (const tc of testCases) {
      test(tc.name, { timeout: TEST_TIMEOUT_MS }, async () => {
        const result = await runTest(tc.name, "max_tokens", {
          prompt: TEST_PROMPT,
          max_tokens: tc.value,
          temperature: 0.7,
        }, TEST_TIMEOUT_MS);
        console.log(`  ${result.supported ? "✅" : "❌"} ${tc.name} | ${result.status} | ${result.elapsedMs}ms${result.error ? ` | ${result.error}` : ""}`);
        expect(result.supported).toBe(true);
      });
    }
  });

  // ══════════════════════════════════════════════════════════════
  // CATEGORY 2: TEMPERATURE RANGE
  // ══════════════════════════════════════════════════════════════

  describe("temperature range", () => {
    const testCases = [
      { name: "temp_0.0", value: 0.0 },   // Deterministic
      { name: "temp_0.3", value: 0.3 },   // Low creativity
      { name: "temp_0.7", value: 0.7 },   // Balanced (default-ish)
      { name: "temp_1.0", value: 1.0 },   // Creative
      { name: "temp_1.2", value: 1.2 },   // High creativity
      { name: "temp_1.5", value: 1.5 },   // Very high
      { name: "temp_2.0", value: 2.0 },   // Maximum
    ];

    for (const tc of testCases) {
      test(tc.name, { timeout: TEST_TIMEOUT_MS }, async () => {
        const result = await runTest(tc.name, "temperature", {
          prompt: TEST_PROMPT,
          max_tokens: 100,
          temperature: tc.value,
        }, TEST_TIMEOUT_MS);
        console.log(`  ${result.supported ? "✅" : "❌"} ${tc.name} | ${result.status} | ${result.elapsedMs}ms${result.error ? ` | ${result.error}` : ""}`);
        expect(result.supported).toBe(true);
      });
    }
  });

  // ══════════════════════════════════════════════════════════════
  // CATEGORY 3: TOP_P (NUCLEUS SAMPLING)
  // ══════════════════════════════════════════════════════════════

  describe("top_p (nucleus sampling)", () => {
    const testCases = [
      { name: "topp_0.1", value: 0.1 },   // Very restrictive
      { name: "topp_0.5", value: 0.5 },   // Moderate
      { name: "topp_0.9", value: 0.9 },   // Standard nucleus
      { name: "topp_0.95", value: 0.95 }, // Common default
      { name: "topp_1.0", value: 1.0 },   // No filtering
    ];

    for (const tc of testCases) {
      test(tc.name, { timeout: TEST_TIMEOUT_MS }, async () => {
        const result = await runTest(tc.name, "top_p", {
          prompt: TEST_PROMPT,
          max_tokens: 100,
          temperature: 0.7,
          top_p: tc.value,
        }, TEST_TIMEOUT_MS);
        console.log(`  ${result.supported ? "✅" : "❌"} ${tc.name} | ${result.status} | ${result.elapsedMs}ms${result.error ? ` | ${result.error}` : ""}`);
        expect(result.supported).toBe(true);
      });
    }
  });

  // ══════════════════════════════════════════════════════════════
  // CATEGORY 4: REASONING EFFORT (NIM-specific via chat_template_kwargs)
  // ══════════════════════════════════════════════════════════════

  describe("reasoning_effort (chat_template_kwargs)", () => {
    const testCases = [
      { name: "reasoning_none", value: "none" },
      { name: "reasoning_low", value: "low" },
      { name: "reasoning_medium", value: "medium" },
      { name: "reasoning_high", value: "high" },
      { name: "reasoning_max", value: "max" },
      { name: "reasoning_xhigh", value: "xhigh" },
    ];

    for (const tc of testCases) {
      test(tc.name, { timeout: TEST_TIMEOUT_MS }, async () => {
        const result = await runTest(tc.name, "reasoning_effort", {
          prompt: TEST_PROMPT,
          max_tokens: 200,
          temperature: 0.7,
          chat_template_kwargs: { reasoning_effort: tc.value },
        }, TEST_TIMEOUT_MS);
        console.log(`  ${result.supported ? "✅" : "❌"} ${tc.name} | ${result.status} | ${result.elapsedMs}ms${result.error ? ` | ${result.error}` : ""}`);
        expect(result.supported).toBe(true);
      });
    }
  });

  // ══════════════════════════════════════════════════════════════
  // CATEGORY 5: TOP-LEVEL REASONING_EFFORT (OpenAI style - should be ignored)
  // ══════════════════════════════════════════════════════════════

  describe("top-level reasoning_effort (OpenAI style)", () => {
    const testCases = [
      { name: "reasoning_toplevel_none", value: "none" },
      { name: "reasoning_toplevel_low", value: "low" },
      { name: "reasoning_toplevel_medium", value: "medium" },
      { name: "reasoning_toplevel_high", value: "high" },
      { name: "reasoning_toplevel_max", value: "max" },
    ];

    for (const tc of testCases) {
      test(tc.name, { timeout: TEST_TIMEOUT_MS }, async () => {
        const result = await runTest(tc.name, "reasoning_effort_toplevel", {
          prompt: TEST_PROMPT,
          max_tokens: 100,
          temperature: 0.7,
          reasoning_effort: tc.value, // Top-level, not in chat_template_kwargs
        }, TEST_TIMEOUT_MS);
        console.log(`  ${result.supported ? "✅" : "❌"} ${tc.name} | ${result.status} | ${result.elapsedMs}ms${result.error ? ` | ${result.error}` : ""}`);
        // This might be ignored but shouldn't error
        expect(result.supported).toBe(true);
      });
    }
  });

  // ══════════════════════════════════════════════════════════════
  // CATEGORY 6: PENALTY PARAMETERS
  // ══════════════════════════════════════════════════════════════

  describe("presence_penalty", () => {
    const testCases = [
      { name: "presence_penalty_-2.0", value: -2.0 },
      { name: "presence_penalty_-1.0", value: -1.0 },
      { name: "presence_penalty_0.0", value: 0.0 },
      { name: "presence_penalty_1.0", value: 1.0 },
      { name: "presence_penalty_2.0", value: 2.0 },
    ];

    for (const tc of testCases) {
      test(tc.name, { timeout: TEST_TIMEOUT_MS }, async () => {
        const result = await runTest(tc.name, "presence_penalty", {
          prompt: TEST_PROMPT,
          max_tokens: 100,
          temperature: 0.7,
          presence_penalty: tc.value,
        }, TEST_TIMEOUT_MS);
        console.log(`  ${result.supported ? "✅" : "❌"} ${tc.name} | ${result.status} | ${result.elapsedMs}ms${result.error ? ` | ${result.error}` : ""}`);
        expect(result.supported).toBe(true);
      });
    }
  });

  describe("frequency_penalty", () => {
    const testCases = [
      { name: "frequency_penalty_-2.0", value: -2.0 },
      { name: "frequency_penalty_-1.0", value: -1.0 },
      { name: "frequency_penalty_0.0", value: 0.0 },
      { name: "frequency_penalty_1.0", value: 1.0 },
      { name: "frequency_penalty_2.0", value: 2.0 },
    ];

    for (const tc of testCases) {
      test(tc.name, { timeout: TEST_TIMEOUT_MS }, async () => {
        const result = await runTest(tc.name, "frequency_penalty", {
          prompt: TEST_PROMPT,
          max_tokens: 100,
          temperature: 0.7,
          frequency_penalty: tc.value,
        }, TEST_TIMEOUT_MS);
        console.log(`  ${result.supported ? "✅" : "❌"} ${tc.name} | ${result.status} | ${result.elapsedMs}ms${result.error ? ` | ${result.error}` : ""}`);
        expect(result.supported).toBe(true);
      });
    }
  });

  // ══════════════════════════════════════════════════════════════
  // CATEGORY 7: STOP SEQUENCES
  // ══════════════════════════════════════════════════════════════

  describe("stop sequences", () => {
    const testCases = [
      { name: "stop_string", value: "STOP" },
      { name: "stop_array", value: ["STOP", "END", "\n\n"] },
    ];

    for (const tc of testCases) {
      test(tc.name, { timeout: TEST_TIMEOUT_MS }, async () => {
        const result = await runTest(tc.name, "stop", {
          prompt: "Count to 10: ",
          max_tokens: 50,
          temperature: 0.7,
          stop: tc.value,
        }, TEST_TIMEOUT_MS);
        console.log(`  ${result.supported ? "✅" : "❌"} ${tc.name} | ${result.status} | ${result.elapsedMs}ms${result.error ? ` | ${result.error}` : ""}`);
        expect(result.supported).toBe(true);
      });
    }
  });

  // ══════════════════════════════════════════════════════════════
  // CATEGORY 8: N (MULTIPLE COMPLETIONS)
  // ══════════════════════════════════════════════════════════════

  describe("n (multiple completions)", () => {
    const testCases = [
      { name: "n_1", value: 1 },
      { name: "n_2", value: 2 },
      { name: "n_3", value: 3 },
    ];

    for (const tc of testCases) {
      test(tc.name, { timeout: TEST_TIMEOUT_MS }, async () => {
        const result = await runTest(tc.name, "n", {
          prompt: TEST_PROMPT,
          max_tokens: 50,
          temperature: 0.7,
          n: tc.value,
        }, TEST_TIMEOUT_MS);
        console.log(`  ${result.supported ? "✅" : "❌"} ${tc.name} | ${result.status} | ${result.elapsedMs}ms${result.error ? ` | ${result.error}` : ""}`);
        expect(result.supported).toBe(true);
      });
    }
  });

  // ══════════════════════════════════════════════════════════════
  // CATEGORY 9: SYSTEM PROMPT
  // ══════════════════════════════════════════════════════════════

  describe("system prompt", () => {
    test("system_prompt_basic", { timeout: TEST_TIMEOUT_MS }, async () => {
      const result = await runTest("system_prompt_basic", "system_prompt", {
        prompt: TEST_PROMPT,
        max_tokens: 100,
        temperature: 0.7,
        system_prompt: "You are a helpful assistant.",
      }, TEST_TIMEOUT_MS);
      console.log(`  ${result.supported ? "✅" : "❌"} system_prompt_basic | ${result.status} | ${result.elapsedMs}ms${result.error ? ` | ${result.error}` : ""}`);
      expect(result.supported).toBe(true);
    });

    test("system_prompt_detailed", { timeout: TEST_TIMEOUT_MS }, async () => {
      const result = await runTest("system_prompt_detailed", "system_prompt", {
        prompt: TEST_PROMPT,
        max_tokens: 100,
        temperature: 0.7,
        system_prompt: "You are a concise assistant. Answer in exactly one sentence.",
      }, TEST_TIMEOUT_MS);
      console.log(`  ${result.supported ? "✅" : "❌"} system_prompt_detailed | ${result.status} | ${result.elapsedMs}ms${result.error ? ` | ${result.error}` : ""}`);
      expect(result.supported).toBe(true);
    });
  });

  // ══════════════════════════════════════════════════════════════
  // CATEGORY 10: LOGPROBS
  // ══════════════════════════════════════════════════════════════

  describe("logprobs", () => {
    const testCases = [
      { name: "logprobs_false", value: false },
      { name: "logprobs_true", value: true },
      { name: "logprobs_true_top5", value: { logprobs: true, top_logprobs: 5 } },
      { name: "logprobs_true_top20", value: { logprobs: true, top_logprobs: 20 } },
    ];

    for (const tc of testCases) {
      test(tc.name, { timeout: TEST_TIMEOUT_MS }, async () => {
        const payload: any = {
          prompt: TEST_PROMPT,
          max_tokens: 50,
          temperature: 0.7,
        };
        if (typeof tc.value === "object") {
          Object.assign(payload, tc.value);
        } else {
          payload.logprobs = tc.value;
        }
        
        const result = await runTest(tc.name, "logprobs", payload, TEST_TIMEOUT_MS);
        console.log(`  ${result.supported ? "✅" : "❌"} ${tc.name} | ${result.status} | ${result.elapsedMs}ms${result.error ? ` | ${result.error}` : ""}`);
        expect(result.supported).toBe(true);
      });
    }
  });

  // ══════════════════════════════════════════════════════════════
  // CATEGORY 11: SEED (DETERMINISTIC OUTPUTS)
  // ══════════════════════════════════════════════════════════════

  describe("seed", () => {
    const testCases = [
      { name: "seed_42", value: 42 },
      { name: "seed_12345", value: 12345 },
      { name: "seed_0", value: 0 },
    ];

    for (const tc of testCases) {
      test(tc.name, { timeout: TEST_TIMEOUT_MS }, async () => {
        const result = await runTest(tc.name, "seed", {
          prompt: TEST_PROMPT,
          max_tokens: 50,
          temperature: 0.7,
          seed: tc.value,
        }, TEST_TIMEOUT_MS);
        console.log(`  ${result.supported ? "✅" : "❌"} ${tc.name} | ${result.status} | ${result.elapsedMs}ms${result.error ? ` | ${result.error}` : ""}`);
        expect(result.supported).toBe(true);
      });
    }
  });

  // ══════════════════════════════════════════════════════════════
  // CATEGORY 12: USER IDENTIFIER
  // ══════════════════════════════════════════════════════════════

  describe("user", () => {
    test("user_string", { timeout: TEST_TIMEOUT_MS }, async () => {
      const result = await runTest("user_string", "user", {
        prompt: TEST_PROMPT,
        max_tokens: 50,
        temperature: 0.7,
        user: "test-user-123",
      }, TEST_TIMEOUT_MS);
      console.log(`  ${result.supported ? "✅" : "❌"} user_string | ${result.status} | ${result.elapsedMs}ms${result.error ? ` | ${result.error}` : ""}`);
      expect(result.supported).toBe(true);
    });
  });

  // ══════════════════════════════════════════════════════════════
  // CATEGORY 13: STREAMING
  // ══════════════════════════════════════════════════════════════

  describe("streaming", () => {
    test("streaming_true", { timeout: TEST_TIMEOUT_MS }, async () => {
      await rateLimit();
      const start = Date.now();
      try {
        const result = await Promise.race([
          llamaSwapChatStream({
            model: INKLING_MODEL,
            prompt: TEST_PROMPT,
            max_tokens: 50,
            temperature: 0.7,
          }),
          new Promise<never>((_, reject) => 
            setTimeout(() => reject(new Error("Streaming test timeout")), TEST_TIMEOUT_MS)
          )
        ]);
        const elapsed = Date.now() - start;
        const supported = result.sse_chunks_with_choices > 0;
        console.log(`  ${supported ? "✅" : "⚠️"} streaming_true | ${elapsed}ms | chunks: ${result.sse_chunks_with_choices}`);
        results.push({
          name: "streaming_true",
          category: "streaming",
          success: supported,
          status: supported ? 200 : 0,
          elapsedMs: elapsed,
          supported,
        });
        // Streaming may not be supported - don't fail
      } catch (e) {
        console.log(`  ⚠️ streaming_true | error: ${e}`);
        results.push({
          name: "streaming_true",
          category: "streaming",
          success: false,
          status: 0,
          elapsedMs: Date.now() - start,
          error: String(e).slice(0, 200),
          supported: false,
        });
      }
    });

    test("streaming_false (explicit)", { timeout: TEST_TIMEOUT_MS }, async () => {
      const result = await runTest("streaming_false", "streaming", {
        prompt: TEST_PROMPT,
        max_tokens: 50,
        temperature: 0.7,
        stream: false,
      }, TEST_TIMEOUT_MS);
      console.log(`  ${result.supported ? "✅" : "❌"} streaming_false | ${result.status} | ${result.elapsedMs}ms${result.error ? ` | ${result.error}` : ""}`);
      expect(result.supported).toBe(true);
    });
  });

  // ══════════════════════════════════════════════════════════════
  // CATEGORY 14: RESPONSE FORMAT
  // ══════════════════════════════════════════════════════════════

  describe("response_format", () => {
    test("response_format_json_object", { timeout: TEST_TIMEOUT_MS }, async () => {
      const result = await runTest("response_format_json_object", "response_format", {
        prompt: 'Output JSON: {"name": "test", "value": 123}',
        max_tokens: 100,
        temperature: 0.1,
        response_format: { type: "json_object" },
      }, TEST_TIMEOUT_MS);
      console.log(`  ${result.supported ? "✅" : "❌"} response_format_json_object | ${result.status} | ${result.elapsedMs}ms${result.error ? ` | ${result.error}` : ""}`);
      expect(result.supported).toBe(true);
    });

    test("response_format_text", { timeout: TEST_TIMEOUT_MS }, async () => {
      const result = await runTest("response_format_text", "response_format", {
        prompt: TEST_PROMPT,
        max_tokens: 50,
        temperature: 0.7,
        response_format: { type: "text" },
      }, TEST_TIMEOUT_MS);
      console.log(`  ${result.supported ? "✅" : "❌"} response_format_text | ${result.status} | ${result.elapsedMs}ms${result.error ? ` | ${result.error}` : ""}`);
      expect(result.supported).toBe(true);
    });
  });

  // ══════════════════════════════════════════════════════════════
  // CATEGORY 15: TOOL CALLING (if supported)
  // ══════════════════════════════════════════════════════════════

  describe("tools / function calling", () => {
    test("tools_basic", { timeout: TEST_TIMEOUT_MS }, async () => {
      const result = await runTest("tools_basic", "tools", {
        prompt: "What's the weather in San Francisco?",
        max_tokens: 100,
        temperature: 0.7,
        tools: [{
          type: "function",
          function: {
            name: "get_weather",
            description: "Get weather for a location",
            parameters: {
              type: "object",
              properties: {
                location: { type: "string", description: "City name" },
              },
              required: ["location"],
            },
          },
        }],
        tool_choice: "auto",
      }, TEST_TIMEOUT_MS);
      console.log(`  ${result.supported ? "✅" : "❌"} tools_basic | ${result.status} | ${result.elapsedMs}ms${result.error ? ` | ${result.error}` : ""}`);
      expect(result.supported).toBe(true);
    });
  });

  // ══════════════════════════════════════════════════════════════
  // CATEGORY 16: EXTRA BODY / CHAT_TEMPLATE_KWARGS EXTENSIONS
  // ══════════════════════════════════════════════════════════════

  describe("extra_body extensions", () => {
    const testCases = [
      { name: "extra_body_reasoning", value: { chat_template_kwargs: { reasoning_effort: "high" } } },
      { name: "extra_body_thinking", value: { chat_template_kwargs: { thinking: true } } },
      { name: "extra_body_continuous", value: { chat_template_kwargs: { continuous_thinking: true } } },
    ];

    for (const tc of testCases) {
      test(tc.name, { timeout: TEST_TIMEOUT_MS }, async () => {
        const result = await runTest(tc.name, "extra_body", {
          prompt: TEST_PROMPT,
          max_tokens: 100,
          temperature: 0.7,
          extra_body: tc.value,
        }, TEST_TIMEOUT_MS);
        console.log(`  ${result.supported ? "✅" : "❌"} ${tc.name} | ${result.status} | ${result.elapsedMs}ms${result.error ? ` | ${result.error}` : ""}`);
        expect(result.supported).toBe(true);
      });
    }
  });

  // ══════════════════════════════════════════════════════════════
  // CATEGORY 17: MAX_COMPLETION_TOKENS (OpenAI new param - should fail)
  // ══════════════════════════════════════════════════════════════

  describe("max_completion_tokens (OpenAI new - expected to fail)", () => {
    const testCases = [
      { name: "max_completion_tokens_100", value: 100 },
      { name: "max_completion_tokens_1000", value: 1000 },
    ];

    for (const tc of testCases) {
      test(tc.name, { timeout: TEST_TIMEOUT_MS }, async () => {
        const result = await runTest(tc.name, "max_completion_tokens", {
          prompt: TEST_PROMPT,
          max_completion_tokens: tc.value,
          temperature: 0.7,
        }, TEST_TIMEOUT_MS);
        console.log(`  ${result.supported ? "✅" : "❌"} ${tc.name} | ${result.status} | ${result.elapsedMs}ms${result.error ? ` | ${result.error}` : ""}`);
        // This is expected to fail/not be supported
      });
    }
  });

  // ══════════════════════════════════════════════════════════════
  // SUMMARY
  // ══════════════════════════════════════════════════════════════

  afterAll(() => {
    console.log("\n" + "=".repeat(80));
    console.log("PARAMETER FUZZ TEST SUMMARY");
    console.log("=".repeat(80));
    
    // Group by category
    const byCategory = new Map<string, TestResult[]>();
    for (const r of results) {
      if (!byCategory.has(r.category)) byCategory.set(r.category, []);
      byCategory.get(r.category)!.push(r);
    }
    
    for (const [category, tests] of byCategory) {
      const supported = tests.filter(t => t.supported).length;
      const total = tests.length;
      console.log(`\n${category.toUpperCase()} (${supported}/${total} supported):`);
      for (const t of tests) {
        const status = t.supported ? "✅" : "❌";
        console.log(`  ${status} ${t.name.padEnd(35)} | ${t.status.toString().padStart(3)} | ${t.elapsedMs.toString().padStart(6)}ms${t.error ? ` | ${t.error}` : ""}`);
      }
    }
    
    console.log("\n" + "=".repeat(80));
    const totalSupported = results.filter(r => r.supported).length;
    console.log(`TOTAL: ${totalSupported}/${results.length} parameters supported`);
    console.log("=".repeat(80));
  });
});