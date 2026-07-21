/**
 * llama_swap_ssot.ts unit tests — covers utility functions, URL builders,
 * pickDefaultModel logic, and oaicopilotModelsFromSwap without live service.
 */
import { describe, test, expect, beforeEach, afterEach, vi } from "bun:test";
import { homedir } from "node:os";
import { join } from "node:path";

const originalFetch = globalThis.fetch;
const mockFetch = vi.fn();

beforeEach(() => {
  mockFetch.mockReset();
  globalThis.fetch = mockFetch;
});

afterEach(() => {
  globalThis.fetch = originalFetch;
});

import {
  swapBaseUrl,
  swapV1Url,
  swapModelsSseUrl,
  listSwapModels,
  pickDefaultModel,
  watchSwapModelsSseRefresh,
  oaicopilotModelsFromSwap,
  openaiCompatClientConfig,
  clientEnvExports,
} from "../src/lib/llama_swap_ssot.ts";

// ── URL builders ─────────────────────────────────────────────────────────────

describe("llama_swap_ssot URL builders", () => {
  test("swapBaseUrl returns http://127.0.0.1:${port}", () => {
    const url = swapBaseUrl();
    expect(url).toMatch(/^http:\/\/127\.0\.0\.1:\d+$/);
  });

  test("swapV1Url appends /v1", () => {
    expect(swapV1Url()).toMatch(/^http:\/\/127\.0\.0\.1:\d+\/v1$/);
  });

  test("swapModelsSseUrl appends /models/sse", () => {
    expect(swapModelsSseUrl()).toMatch(
      /^http:\/\/127\.0\.0\.1:\d+\/models\/sse$/,
    );
  });
});

// ── listSwapModels ───────────────────────────────────────────────────────────

describe("listSwapModels", () => {
  test("returns ok + models on 200", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          data: [{ id: "m1", name: "Model 1" }, { id: "m2" }],
        }),
    });
    const { ok, models } = await listSwapModels();
    expect(ok).toBe(true);
    expect(models).toHaveLength(2);
    expect(models[0].id).toBe("m1");
    expect(models[0].name).toBe("Model 1");
  });

  test("returns error on HTTP non-200 (line 46)", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 503 });
    const { ok, models, error } = await listSwapModels();
    expect(ok).toBe(false);
    expect(models).toEqual([]);
    expect(error).toContain("503");
  });

  test("returns error on fetch exception (line 57)", async () => {
    mockFetch.mockRejectedValueOnce(new Error("ECONNREFUSED"));
    const { ok, models, error } = await listSwapModels();
    expect(ok).toBe(false);
    expect(models).toEqual([]);
    expect(error).toContain("ECONNREFUSED");
  });

  test("maps model status.value correctly (line 52)", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          data: [{ id: "m1", status: { value: "loaded" } }],
        }),
    });
    const { models } = await listSwapModels();
    expect(models[0].status).toBe("loaded");
  });

  test("passes through status string when not object (line 52)", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          data: [{ id: "m1", status: "unloaded" }],
        }),
    });
    const { models } = await listSwapModels();
    expect(models[0].status).toBe("unloaded");
  });

  test("preserves meta field (line 53)", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          data: [{ id: "m1", meta: { ctx: 8192 } }],
        }),
    });
    const { models } = await listSwapModels();
    expect(models[0].meta).toEqual({ ctx: 8192 });
  });

  test("handles missing data array (line 49)", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({}),
    });
    const { ok, models } = await listSwapModels();
    expect(ok).toBe(true);
    expect(models).toEqual([]);
  });
});

// ── pickDefaultModel ─────────────────────────────────────────────────────────

describe("pickDefaultModel", () => {
  test("prefers loaded model over others (line 67-70)", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          data: [{ id: "model-a" }, { id: "model-b", status: "loaded" }],
        }),
    });
    const result = await pickDefaultModel();
    expect(result).toBe("model-b");
  });

  test("skips MODEL_PLACEHOLDER (line 68)", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          data: [
            { id: "MODEL_PLACEHOLDER_1", status: "loaded" },
            { id: "real-model" },
          ],
        }),
    });
    const result = await pickDefaultModel();
    expect(result).toBe("real-model");
  });

  test("returns preferred if in catalog (line 71)", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          data: [{ id: "beellama/qwen-flash-64k" }],
        }),
    });
    const result = await pickDefaultModel();
    expect(result).toBe("beellama/qwen-flash-64k");
  });

  test("returns preferred when empty catalog (line 66)", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ data: [] }),
    });
    const result = await pickDefaultModel("my-preferred");
    expect(result).toBe("my-preferred");
  });

  test("returns first non-placeholder when preferred not in catalog (line 72-73)", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          data: [{ id: "MODEL_PLACEHOLDER_1" }, { id: "actual-model" }],
        }),
    });
    const result = await pickDefaultModel("nonexistent");
    expect(result).toBe("actual-model");
  });

  test("uses LLAMA_SWAP_MODEL env as preferred (line 63)", async () => {
    const orig = process.env.LLAMA_SWAP_MODEL;
    process.env.LLAMA_SWAP_MODEL = "env-model";
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ data: [{ id: "env-model" }] }),
    });
    const result = await pickDefaultModel();
    expect(result).toBe("env-model");
    if (orig !== undefined) process.env.LLAMA_SWAP_MODEL = orig;
    else delete process.env.LLAMA_SWAP_MODEL;
  });
});

// ── oaicopilotModelsFromSwap ─────────────────────────────────────────────────

describe("oaicopilotModelsFromSwap", () => {
  test("maps SwapModel[] to oaicopilot shape", () => {
    const models = [
      { id: "beellama/qwen-flash-64k", name: "Qwen Flash" },
      { id: "beellama/gemma3-27b-it" },
    ];
    const result = oaicopilotModelsFromSwap(models);
    expect(result).toHaveLength(2);
    expect(result[0].id).toBe("beellama/qwen-flash-64k");
    expect(result[0].displayName).toBe("local/qwen-flash-64k");
    expect(result[0].owned_by).toBe("llama-swap");
    expect(result[0].context_length).toBe(65536);
    expect(result[0].vision).toBe(false);
  });

  test("detects vision from gemma in id", () => {
    const models = [{ id: "model/gemma3-4b" }];
    const result = oaicopilotModelsFromSwap(models);
    expect(result[0].vision).toBe(true);
  });

  test("filters out MODEL_PLACEHOLDER entries", () => {
    const models = [{ id: "MODEL_PLACEHOLDER_1" }, { id: "real-model" }];
    const result = oaicopilotModelsFromSwap(models);
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe("real-model");
  });

  test("context length parsed from model name (512k)", () => {
    const models = [{ id: "some/model-512k" }];
    const result = oaicopilotModelsFromSwap(models);
    expect(result[0].context_length).toBe(524288);
  });

  test("context length defaults to 65536 when no match", () => {
    const models = [{ id: "some/model" }];
    const result = oaicopilotModelsFromSwap(models);
    expect(result[0].context_length).toBe(65536);
  });

  test("uses custom base URL", () => {
    const models = [{ id: "m1" }];
    const result = oaicopilotModelsFromSwap(models, "http://custom:9999/v1");
    expect(result[0].baseUrl).toBe("http://custom:9999/v1");
  });
});

// ── openaiCompatClientConfig ─────────────────────────────────────────────────

describe("openaiCompatClientConfig", () => {
  test("returns correct structure with defaults", () => {
    const config = openaiCompatClientConfig();
    expect(config.base_url).toMatch(/^http:\/\/127\.0\.0\.1:\d+\/v1$/);
    expect(config.api_key).toBe("not-required-for-local");
    expect(config.default_model).toBe("beellama/qwen-flash-64k");
    expect(config.models_url).toContain("/models");
    expect(config.models_sse_url).toContain("/models/sse");
  });

  test("uses custom default model", () => {
    const config = openaiCompatClientConfig("custom-model");
    expect(config.default_model).toBe("custom-model");
  });
});

// ── clientEnvExports ─────────────────────────────────────────────────────────

describe("clientEnvExports", () => {
  test("returns shell exports with all env vars", () => {
    const output = clientEnvExports();
    expect(output).toContain("export OPENAI_BASE_URL=");
    expect(output).toContain("export LLAMA_SWAP_URL=");
    expect(output).toContain("export LLAMA_CHAT_URL=");
    expect(output).toContain("export SOVEREIGN_LLM=");
    expect(output).toContain("export LLAMA_MODELS_SSE_URL=");
  });

  test("uses custom default model in LLAMA_SWAP_MODEL", () => {
    const output = clientEnvExports("custom-model");
    expect(output).toContain("export LLAMA_SWAP_MODEL=custom-model");
  });

  test("contains do-not-edit comment", () => {
    expect(clientEnvExports()).toContain("do not hand-edit");
  });
});

// ── watchSwapModelsSseRefresh ─────────────────────────────────────────────────

describe("watchSwapModelsSseRefresh", () => {
  test("returns abort handle", () => {
    mockFetch.mockResolvedValue({ ok: false, body: null });
    const h = watchSwapModelsSseRefresh(() => {});
    expect(typeof h.abort).toBe("function");
    h.abort();
  });

  test("abort stops gracefully (double abort safe)", () => {
    mockFetch.mockResolvedValue({ ok: false, body: null });
    const h = watchSwapModelsSseRefresh(() => {});
    h.abort();
    h.abort(); // should not throw
  });
});

// ── watchSwapModelsSse (SSE reader loop coverage, lines 86-128) ────────────

describe("watchSwapModelsSse — SSE reader loop", () => {
  test("reads SSE events and calls onEvent (lines 100-117)", async () => {
    const events = [
      'data: {"model":"m1","event":"loaded"}',
      'data: {"model":"m2","event":"unloaded"}',
      "data: [DONE]",
    ].join("\n\n");

    // Create a mock ReadableStream
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode(events));
        controller.close();
      },
    });

    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: stream,
    });

    const received: any[] = [];
    // Import watchSwapModelsSse directly
    const { watchSwapModelsSse } =
      await import("../src/lib/llama_swap_ssot.ts");
    const h = watchSwapModelsSse((ev) => received.push(ev));

    // Give the async reader time to process
    await new Promise((r) => setTimeout(r, 100));
    h.abort();

    expect(received.length).toBeGreaterThanOrEqual(1);
    expect(received[0].model).toBe("m1");
  });

  test("calls onError on HTTP non-200 (line 98)", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 503,
      body: null,
    });
    let errorCaught: any = null;
    const { watchSwapModelsSse } =
      await import("../src/lib/llama_swap_ssot.ts");
    watchSwapModelsSse(
      () => {},
      (e) => {
        errorCaught = e;
      },
    );
    await new Promise((r) => setTimeout(r, 50));
    expect(errorCaught).toBeTruthy();
    expect(String(errorCaught)).toContain("503");
  });

  test("calls onError on fetch exception (lines 123-124)", async () => {
    mockFetch.mockRejectedValueOnce(new Error("network fail"));
    let errorCaught: any = null;
    const { watchSwapModelsSse } =
      await import("../src/lib/llama_swap_ssot.ts");
    watchSwapModelsSse(
      () => {},
      (e) => {
        errorCaught = e;
      },
    );
    await new Promise((r) => setTimeout(r, 50));
    expect(errorCaught).toBeTruthy();
    expect(String(errorCaught)).toContain("network fail");
  });

  test("skips malformed JSON in SSE data (line 117 catch)", async () => {
    const events = [
      "data: not-valid-json{{{",
      'data: {"model":"ok","event":"loaded"}',
      "data: [DONE]",
    ].join("\n\n");

    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode(events));
        controller.close();
      },
    });
    mockFetch.mockResolvedValueOnce({ ok: true, body: stream });

    const received: any[] = [];
    const { watchSwapModelsSse } =
      await import("../src/lib/llama_swap_ssot.ts");
    const h = watchSwapModelsSse((ev) => received.push(ev));
    await new Promise((r) => setTimeout(r, 100));
    h.abort();

    // Only the valid JSON event should be received
    expect(received.length).toBe(1);
    expect(received[0].model).toBe("ok");
  });

  test("skips keep-alive and empty data lines (line 114)", async () => {
    const events = [": keep-alive", "data: ", "data: [DONE]"].join("\n\n");

    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode(events));
        controller.close();
      },
    });
    mockFetch.mockResolvedValueOnce({ ok: true, body: stream });

    const received: any[] = [];
    const { watchSwapModelsSse } =
      await import("../src/lib/llama_swap_ssot.ts");
    const h = watchSwapModelsSse((ev) => received.push(ev));
    await new Promise((r) => setTimeout(r, 100));
    h.abort();

    expect(received.length).toBe(0);
  });
});

// ── watchSwapModelsSseRefresh debounce coverage (lines 135-155) ────────────

describe("watchSwapModelsSseRefresh — debounce", () => {
  test("calls onRefresh after debounce when SSE fires (lines 141-146)", async () => {
    const encoder = new TextEncoder();
    const sseData = 'data: {"model":"m1","event":"loaded"}\n\n';
    const stream = new ReadableStream({
      start(controller) {
        // Push data immediately — no async delay
        controller.enqueue(encoder.encode(sseData));
        // Keep stream open briefly
        setTimeout(() => controller.close(), 100);
      },
    });
    mockFetch.mockResolvedValue({ ok: true, body: stream });

    let refreshCount = 0;
    const h = watchSwapModelsSseRefresh(
      () => {
        refreshCount++;
      },
      { debounceMs: 100 },
    );

    // Wait for: SSE read + 100ms debounce + margin
    await new Promise((r) => setTimeout(r, 600));
    h.abort();

    expect(refreshCount).toBeGreaterThanOrEqual(1);
  });

  test("debounce coalesces rapid events (line 141-142)", async () => {
    const encoder = new TextEncoder();
    let streamController: ReadableStreamDefaultController | null = null;
    const stream = new ReadableStream({
      start(controller) {
        streamController = controller;
      },
    });
    mockFetch.mockResolvedValue({ ok: true, body: stream });

    let refreshCount = 0;
    const h = watchSwapModelsSseRefresh(
      () => {
        refreshCount++;
      },
      { debounceMs: 100 },
    );

    // Give SSE connection time to establish
    await new Promise((r) => setTimeout(r, 100));

    // Push multiple events rapidly
    const events = [
      'data: {"model":"m1","event":"loaded"}',
      'data: {"model":"m2","event":"loaded"}',
      'data: {"model":"m3","event":"loaded"}',
    ].join("\n\n");
    streamController!.enqueue(encoder.encode(events));
    streamController!.close();

    // Wait for debounce
    await new Promise((r) => setTimeout(r, 500));
    h.abort();

    // Should only fire once due to debounce coalescing
    expect(refreshCount).toBe(1);
  });

  test("abort clears pending debounce timer (line 151)", async () => {
    mockFetch.mockResolvedValue({ ok: false, body: null });

    let refreshCount = 0;
    const h = watchSwapModelsSseRefresh(
      () => {
        refreshCount++;
      },
      { debounceMs: 200 },
    );

    // Abort immediately — timer should be cleared
    h.abort();
    await new Promise((r) => setTimeout(r, 300));
    expect(refreshCount).toBe(0);
  });
});
