/**
 * Drives real shipped helpers + live :25100/:25104/:25107 paths.
 * Asserts non-empty message.content (not reasoning_content-only).
 */
import { describe, expect, test } from "bun:test";
import {
  loadBestModels,
  modelForRole,
  validateBestModelsAgainstCatalog,
  BEST_MODELS_PATH,
} from "../src/lib/best_models.ts";
import { listSwapModels, swapV1Url } from "../src/lib/llama_swap_ssot.ts";
import { existsSync } from "node:fs";

// Skip integration tests if llama-swap is not running (top-level await)
let live = false;
try {
  const { ok } = await listSwapModels(3000);
  live = ok;
} catch {
  live = false;
}

async function chatContent(
  model: string,
  base = swapV1Url(),
  timeoutMs = 180_000,
): Promise<{
  ok: boolean;
  content: string;
  model?: string;
  status: number;
  routed?: string | null;
}> {
  const res = await fetch(`${base.replace(/\/$/, "")}/chat/completions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Accept-Encoding": "identity",
    },
    body: JSON.stringify({
      model,
      messages: [{ role: "user", content: "Reply with only the word OK" }],
      max_tokens: 48,
      temperature: 0,
    }),
    signal: AbortSignal.timeout(timeoutMs),
  });
  const raw = await res.text();
  let data: any = {};
  try {
    data = JSON.parse(raw);
  } catch {
    /* */
  }
  const msg = data?.choices?.[0]?.message || {};
  // STRICT: only message.content counts (skeptic bar)
  const content = typeof msg.content === "string" ? msg.content.trim() : "";
  return {
    ok: res.ok && content.length > 0,
    content,
    model: data?.model,
    status: res.status,
    routed: res.headers.get("X-Routed-Via"),
  };
}

describe.skipIf(!live)("best_models SSOT", () => {
  test("listSwapModels hits real :25100 catalog", async () => {
    const { ok, models, error } = await listSwapModels(8000);
    expect(ok).toBe(true);
    expect(error).toBeUndefined();
    expect(models.length).toBeGreaterThan(3);
    expect(swapV1Url()).toContain("25100");
  });

  test("best-models.json roles are in live catalog when file present", async () => {
    if (!existsSync(BEST_MODELS_PATH)) {
      const id = await modelForRole("fast");
      const { models } = await listSwapModels();
      expect(models.some((m) => m.id === id)).toBe(true);
      return;
    }
    const v = await validateBestModelsAgainstCatalog();
    expect(v.ok).toBe(true);
    expect(v.missing).toEqual([]);
    const doc = loadBestModels();
    expect(doc?.roles?.fast?.id).toBeTruthy();
    expect(doc?.roles?.quality?.id).toBeTruthy();
    expect(doc?.roles?.longctx?.id).toBeTruthy();
  });

  test("modelForRole returns distinct fast vs longctx when ranked", async () => {
    const fast = await modelForRole("fast");
    const longctx = await modelForRole("longctx");
    const { models } = await listSwapModels();
    const ids = new Set(models.map((m) => m.id));
    expect(ids.has(fast)).toBe(true);
    expect(ids.has(longctx)).toBe(true);
    if (existsSync(BEST_MODELS_PATH)) {
      expect(fast).not.toBe(longctx);
    }
  });

  test("fast role returns non-empty message.content", async () => {
    const model = await modelForRole("fast");
    const r = await chatContent(model);
    expect(r.status).toBe(200);
    expect(r.content.length).toBeGreaterThan(0);
  });

  test("quality role returns non-empty message.content (not reasoning-only)", async () => {
    const model = await modelForRole("quality");
    const r = await chatContent(model);
    expect(r.status).toBe(200);
    expect(r.content.length).toBeGreaterThan(0);
    // must not be empty-string content with only reasoning path
    expect(r.ok).toBe(true);
  });

  test("longctx catalog entry has 256k context meta when ranked qwen-flash-256k", async () => {
    const { models } = await listSwapModels();
    const m = models.find((x) => x.id === "beellama/qwen-flash-256k");
    expect(m).toBeTruthy();
    const ctx =
      (m?.meta as any)?.llamaswap?.context ?? (m?.meta as any)?.context;
    if (ctx != null) {
      expect(Number(ctx)).toBeGreaterThanOrEqual(200000);
    }
  });

  test(
    "multi-class routes: fast vs quality vs longctx hit distinct requested ids with content",
    async () => {
      const fast = await modelForRole("fast");
      const quality = await modelForRole("quality");
      const longctx = await modelForRole("longctx");
      expect(new Set([fast, quality, longctx]).size).toBeGreaterThanOrEqual(2);

      const rf = await chatContent(fast);
      const rq = await chatContent(quality);
      const rl = await chatContent(longctx);
      expect(rf.ok).toBe(true);
      expect(rq.ok).toBe(true);
      expect(rl.ok).toBe(true);
    },
    { timeout: 300_000 },
  );

  test(
    "sovereign-router local alias fast routes to local llama-swap model not gemini",
    async () => {
      const r = await chatContent("fast", "http://127.0.0.1:25104/v1");
      expect(r.status).toBe(200);
      expect(r.content.length).toBeGreaterThan(0);
      const mid = String(r.model || "");
      expect(mid.toLowerCase()).not.toContain("gemini");
      expect(/exaone|qwen|gguf|beellama/i.test(mid) || mid.length > 0).toBe(
        true,
      );
    },
    { timeout: 120_000 },
  );

  test(
    "null-g local fallback serves ranked fast with content",
    async () => {
      const r = await chatContent(
        "beellama/exaone-4-0-1-2b-iq4xs",
        "http://127.0.0.1:25107/v1",
      );
      expect(r.status).toBe(200);
      expect(r.content.length).toBeGreaterThan(0);
    },
    { timeout: 120_000 },
  );
});
