/**
 * Drives real shipped helpers against live llama-swap when available.
 * No hard-coded expected latency; asserts catalog membership + role resolution.
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

describe("best_models SSOT", () => {
  test("listSwapModels hits real :25100 catalog", async () => {
    const { ok, models, error } = await listSwapModels(8000);
    expect(ok).toBe(true);
    expect(error).toBeUndefined();
    expect(models.length).toBeGreaterThan(3);
    expect(swapV1Url()).toContain("25100");
  });

  test("best-models.json roles are in live catalog when file present", async () => {
    if (!existsSync(BEST_MODELS_PATH)) {
      // still prove role helper returns catalog member
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
    // when SSOT ranked file exists, roles should differ
    if (existsSync(BEST_MODELS_PATH)) {
      expect(fast).not.toBe(longctx);
    }
  });

  test("short chat on fast role returns non-empty text", async () => {
    const model = await modelForRole("fast");
    const res = await fetch(`${swapV1Url()}/chat/completions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept-Encoding": "identity",
      },
      body: JSON.stringify({
        model,
        messages: [{ role: "user", content: "Say OK" }],
        max_tokens: 16,
        temperature: 0,
      }),
      signal: AbortSignal.timeout(120_000),
    });
    expect(res.ok).toBe(true);
    const data: any = await res.json();
    const msg = data?.choices?.[0]?.message || {};
    const text = (msg.content || msg.reasoning_content || "").trim();
    expect(text.length).toBeGreaterThan(0);
  });
});
