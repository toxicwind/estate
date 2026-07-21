/**
 * llama_swap.ts unit tests — covers httpJson, llamaSwapHealth, llamaSwapModels,
 * llamaSwapChat, llamaSwapChatStream, upstreamServers without hitting a live service.
 *
 * Strategy: mock globalThis.fetch to intercept all HTTP calls.
 */
import { describe, test, expect, beforeEach, afterEach, vi } from "bun:test";
import { loadSovereignPorts } from "../src/lib/ports.ts";

const originalFetch = globalThis.fetch;
const mockFetch = vi.fn();

beforeEach(() => {
  mockFetch.mockReset();
  globalThis.fetch = mockFetch;
});

afterEach(() => {
  globalThis.fetch = originalFetch;
});

// Import AFTER mock setup
import {
  llamaSwapHealth,
  llamaSwapModels,
  llamaSwapChat,
  llamaSwapChatStream,
  upstreamServers,
} from "../src/mcp/llama_swap.ts";

// ── Helpers ──────────────────────────────────────────────────────────────────
function mockFetchJson(data: unknown, status = 200) {
  mockFetch.mockResolvedValueOnce({
    ok: status >= 200 && status < 300,
    status,
    text: () => Promise.resolve(JSON.stringify(data)),
    json: () => Promise.resolve(data),
  });
}

function mockFetchText(text: string, status = 200) {
  mockFetch.mockResolvedValueOnce({
    ok: status >= 200 && status < 300,
    status,
    text: () => Promise.resolve(text),
    json: () => Promise.resolve(JSON.parse(text)),
  });
}

function mockFetchError(msg = "ECONNREFUSED") {
  mockFetch.mockRejectedValueOnce(new Error(msg));
}

function mockFetchTimeout() {
  mockFetch.mockRejectedValueOnce(new Error("Aborted"));
}

// ═══════════════════════════════════════════════════════════════════════════════
describe("llamaSwapHealth", () => {
  test("returns 200 with parsed body", async () => {
    mockFetchJson({ status: "ok" }, 200);
    const r = await llamaSwapHealth();
    expect(r.http_status).toBe(200);
    expect(r.body).toEqual({ status: "ok" });
  });

  test("returns non-200 status", async () => {
    mockFetchJson({ error: "down" }, 503);
    const r = await llamaSwapHealth();
    expect(r.http_status).toBe(503);
  });

  test("handles network error gracefully", async () => {
    mockFetchError("ECONNREFUSED");
    const r = await llamaSwapHealth();
    expect(r.http_status).toBe(0);
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
describe("llamaSwapModels", () => {
  test("parses models with status.value unwrapping (line 69-71)", async () => {
    mockFetchJson({
      data: [
        { id: "model-a", status: { value: "loaded" } },
        { id: "model-b", status: "unloaded" },
        { id: "model-c" },
      ],
    }, 200);
    const r = await llamaSwapModels();
    expect(r.http_status).toBe(200);
    expect((r as any).count).toBe(3);
    expect((r as any).models[0].status).toBe("loaded");
    expect((r as any).models[1].status).toBe("unloaded");
    expect((r as any).models[2].status).toBeUndefined();
  });

  test("returns error for non-object response (line 63-64)", async () => {
    mockFetchText("not json at all", 200);
    const r = await llamaSwapModels();
    expect(r.http_status).toBe(200);
    expect((r as any).error).toBeTruthy();
  });

  test("handles empty data array", async () => {
    mockFetchJson({ data: [] }, 200);
    const r = await llamaSwapModels();
    expect((r as any).count).toBe(0);
    expect((r as any).models).toEqual([]);
  });

  test("handles missing data field", async () => {
    mockFetchJson({}, 200);
    const r = await llamaSwapModels();
    expect((r as any).count).toBe(0);
  });

  test("handles network error", async () => {
    mockFetchError("timeout");
    const r = await llamaSwapModels();
    expect(r.http_status).toBe(0);
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
describe("llamaSwapChat", () => {
  test("successful chat with message.content (lines 99-112)", async () => {
    mockFetchJson({
      choices: [{ message: { content: "Hello!" } }],
      model: "test-model",
    }, 200);
    const r = await llamaSwapChat({ prompt: "Hi" });
    expect(r.ok).toBe(true);
    expect((r as any).choices_count).toBe(1);
    expect((r as any).content_preview).toBe("Hello!");
    expect((r as any).model_returned).toBe("test-model");
  });

  test("successful chat with delta.content (line 101)", async () => {
    mockFetchJson({
      choices: [{ delta: { content: "Chunked reply" } }],
      model: "test-model",
    }, 200);
    const r = await llamaSwapChat({ prompt: "Hi" });
    expect(r.ok).toBe(true);
    expect((r as any).content_preview).toBe("Chunked reply");
  });

  test("non-JSON response returns reason (lines 93-94)", async () => {
    mockFetchText("<html>502 Bad Gateway</html>", 502);
    const r = await llamaSwapChat({ prompt: "Hi" });
    expect(r.ok).toBe(false);
    expect((r as any).reason).toBe("non_json_or_empty");
    expect((r as any).raw_prefix).toContain("502");
  });

  test("empty choices returns ok=false (line 98)", async () => {
    mockFetchJson({ choices: [], model: "x" }, 200);
    const r = await llamaSwapChat({ prompt: "Hi" });
    expect(r.ok).toBe(false);
    expect((r as any).choices_count).toBe(0);
  });

  test("error in response body is propagated (line 111)", async () => {
    mockFetchJson({ error: "rate limited" }, 429);
    const r = await llamaSwapChat({ prompt: "Hi" });
    expect((r as any).error).toBe("rate limited");
  });

  test("defaults when no opts provided", async () => {
    mockFetchJson({
      choices: [{ message: { content: "OK" } }],
      model: "default",
    }, 200);
    const r = await llamaSwapChat({});
    expect(r.ok).toBe(true);
    // Verify default model was used in the request
    const callBody = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(callBody.model).toBe("beellama/qwen-flash-64k");
    expect(callBody.max_tokens).toBe(16);
    expect(callBody.stream).toBe(false);
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
describe("llamaSwapChatStream", () => {
  test("parses SSE chunks with choices (lines 131-146)", async () => {
    const sseData = [
      'data: {"choices":[{"delta":{"content":"Hi"}}]}',
      'data: {"choices":[{"delta":{"content":" there"}}]}',
      "data: [DONE]",
    ].join("\n");
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: () => Promise.resolve(sseData),
    });
    const r = await llamaSwapChatStream({ prompt: "Hi" });
    expect(r.ok).toBe(true);
    expect((r as any).sse_chunks_with_choices).toBe(2);
    expect((r as any).samples.length).toBe(2);
  });

  test("skips non-data lines and malformed JSON (lines 133-144)", async () => {
    const sseData = [
      ": keep-alive",
      "",
      "data: not-json-{{}}",
      'data: {"choices":[{"delta":{"content":"OK"}}]}',
      "data: [DONE]",
    ].join("\n");
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: () => Promise.resolve(sseData),
    });
    const r = await llamaSwapChatStream({ prompt: "Hi" });
    expect(r.ok).toBe(true);
    expect((r as any).sse_chunks_with_choices).toBe(1);
  });

  test("handles fetch error (line 147-148)", async () => {
    mockFetchError("ECONNREFUSED");
    const r = await llamaSwapChatStream({ prompt: "Hi" });
    expect(r.ok).toBe(false);
    expect((r as any).error).toContain("ECONNREFUSED");
  });

  test("caps samples at 3 (line 142)", async () => {
    const sseData = Array.from({ length: 5 }, (_, i) =>
      `data: {"choices":[{"delta":{"content":"chunk${i}"}}]}`
    ).join("\n") + "\ndata: [DONE]";
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: () => Promise.resolve(sseData),
    });
    const r = await llamaSwapChatStream({ prompt: "Hi" });
    expect((r as any).sse_chunks_with_choices).toBe(5);
    expect((r as any).samples.length).toBe(3);
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
describe("upstreamServers", () => {
  test("health operation delegates to llamaSwapHealth (line 155)", async () => {
    mockFetchJson({ status: "ok" }, 200);
    const r = await upstreamServers({ operation: "health" });
    expect((r as any).http_status).toBe(200);
  });

  test("list operation delegates to llamaSwapModels (line 156)", async () => {
    mockFetchJson({ data: [{ id: "m1" }] }, 200);
    const r = await upstreamServers({ operation: "list" });
    expect((r as any).count).toBe(1);
  });

  test("get operation finds a model (lines 157-161)", async () => {
    mockFetchJson({
      data: [{ id: "target-model", status: "loaded" }, { id: "other" }],
    }, 200);
    const r = await upstreamServers({ operation: "get", name: "target-model" });
    expect((r as any).found).toBeTruthy();
    expect((r as any).found.id).toBe("target-model");
  });

  test("get operation returns error when model not found (line 160)", async () => {
    mockFetchJson({ data: [{ id: "other" }] }, 200);
    const r = await upstreamServers({ operation: "get", name: "missing" });
    expect((r as any).error).toContain("not found");
    expect((r as any).available).toBeTruthy();
  });

  test("invalid operation returns error (line 162)", async () => {
    const r = await upstreamServers({ operation: "bogus" as any });
    expect((r as any).error).toBe("invalid operation");
  });
});
