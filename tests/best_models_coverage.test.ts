/**
 * best_models.ts unit tests — covers modelForRole, validateBestModelsAgainstCatalog,
 * watchBestModelsSse without hitting a live service.
 *
 * Strategy: write test data to the REAL BEST_MODELS_PATH (the module-level const
 * is evaluated at import time and cannot be overridden). Mock globalThis.fetch
 * to intercept listSwapModels HTTP calls. No vi.mock needed — avoids Bun's
 * cross-module mock path resolution issues.
 */
import { describe, test, expect, beforeEach, afterEach, vi } from "bun:test";
import { join } from "node:path";
import {
  existsSync,
  writeFileSync,
  mkdirSync,
  rmSync,
  readFileSync,
} from "node:fs";
import { homedir } from "node:os";

// ── Real BEST_MODELS_PATH (const inside best_models.ts, evaluated at import) ─
const SOV = join(homedir(), "sovereign");
const REAL_PATH = join(SOV, ".state/best-models.json");

// ── Backup / restore real file across tests ──────────────────────────────────
let backup: string | null = null;
const originalFetch = globalThis.fetch;
const mockFetch = vi.fn();

beforeEach(() => {
  backup = existsSync(REAL_PATH) ? readFileSync(REAL_PATH, "utf8") : null;
  globalThis.fetch = mockFetch;
  mockFetch.mockReset();
});

afterEach(() => {
  // Restore real file
  if (backup !== null) {
    writeFileSync(REAL_PATH, backup);
  } else if (existsSync(REAL_PATH)) {
    rmSync(REAL_PATH);
  }
  globalThis.fetch = originalFetch;
});

// ── Import AFTER mock setup so module-level code runs with mocked fetch ──────
import {
  loadBestModels,
  modelForRole,
  validateBestModelsAgainstCatalog,
  watchBestModelsSse,
} from "../src/lib/best_models.ts";

// ── Helpers ──────────────────────────────────────────────────────────────────
function writeTestDoc(doc: Record<string, unknown>) {
  mkdirSync(join(REAL_PATH, ".."), { recursive: true });
  writeFileSync(REAL_PATH, JSON.stringify(doc));
}

function mockListSwapModels(
  models: { id: string; status?: string }[],
  opts: { ok?: boolean } = {},
) {
  mockFetch.mockResolvedValueOnce({
    ok: opts.ok ?? true,
    json: () => Promise.resolve({ data: models }),
  });
}

function mockListSwapFail(status = 503) {
  mockFetch.mockResolvedValueOnce({
    ok: false,
    status,
    json: () => Promise.resolve({}),
  });
}

function mockListSwapError(msg = "fetch failed") {
  mockFetch.mockRejectedValueOnce(new Error(msg));
}

// ═══════════════════════════════════════════════════════════════════════════════
describe("best_models.ts coverage", () => {
  // ── loadBestModels (pure, no network) ───────────────────────────────────────

  test("loadBestModels returns null for non-existent file", () => {
    expect(loadBestModels("/nonexistent/path.json")).toBeNull();
  });

  test("loadBestModels returns null for invalid JSON (line 41 catch)", () => {
    const badPath = join(SOV, ".state", `bad-test-${Date.now()}.json`);
    mkdirSync(join(badPath, ".."), { recursive: true });
    writeFileSync(badPath, "not valid json {{{");
    expect(loadBestModels(badPath)).toBeNull();
    rmSync(badPath);
  });

  test("loadBestModels parses valid JSON", () => {
    const doc = {
      ts: "2024-01-01",
      roles: { fast: { id: "test-model" } },
    };
    writeTestDoc(doc);
    expect(loadBestModels(REAL_PATH)).toEqual(doc);
  });

  // ── modelForRole("default") — cascading fallback (lines 51-56) ──────────────

  test("modelForRole default uses recommended.default_chat (line 52)", async () => {
    writeTestDoc({ recommended: { default_chat: "rec-model" } });
    expect(await modelForRole("default")).toBe("rec-model");
  });

  test("modelForRole default falls back to roles.quality.id (line 54)", async () => {
    writeTestDoc({ roles: { quality: { id: "qual-model" } } });
    expect(await modelForRole("default")).toBe("qual-model");
  });

  test("modelForRole default falls back to pickDefaultModel (line 55)", async () => {
    writeTestDoc({});
    // pickDefaultModel → listSwapModels → fetch → return loaded model
    mockListSwapModels([{ id: "beellama/qwen-flash-64k", status: "loaded" }]);
    const result = await modelForRole("default");
    expect(result).toBe("beellama/qwen-flash-64k");
  });

  test("modelForRole default falls back to hardcoded when no models (line 55)", async () => {
    writeTestDoc({});
    mockListSwapModels([]);
    const result = await modelForRole("default");
    expect(result).toBe("beellama/qwen-flash-64k");
  });

  // ── modelForRole("fast") — catalog check + fallback (lines 58-64) ───────────

  test("modelForRole fast returns doc id when in catalog (line 58-61)", async () => {
    writeTestDoc({ roles: { fast: { id: "fast-model" } } });
    mockListSwapModels([{ id: "fast-model" }]);
    expect(await modelForRole("fast")).toBe("fast-model");
  });

  test("modelForRole fast falls back to hardcoded when not in catalog (line 64)", async () => {
    writeTestDoc({ roles: { fast: { id: "not-in-catalog" } } });
    mockListSwapModels([{ id: "other-model" }]);
    expect(await modelForRole("fast")).toBe("beellama/exaone-4-0-1-2b-iq4xs");
  });

  test("modelForRole fast falls back to hardcoded when no roles", async () => {
    writeTestDoc({});
    mockListSwapModels([{ id: "anything" }]);
    expect(await modelForRole("fast")).toBe("beellama/exaone-4-0-1-2b-iq4xs");
  });

  // ── modelForRole("longctx") — fallback (line 65) ────────────────────────────

  test("modelForRole longctx returns doc id when in catalog", async () => {
    writeTestDoc({ roles: { longctx: { id: "long-model" } } });
    mockListSwapModels([{ id: "long-model" }]);
    expect(await modelForRole("longctx")).toBe("long-model");
  });

  test("modelForRole longctx falls back to hardcoded (line 65)", async () => {
    writeTestDoc({ roles: { longctx: { id: "not-in-catalog" } } });
    mockListSwapModels([{ id: "other-model" }]);
    expect(await modelForRole("longctx")).toBe("beellama/qwen-flash-256k");
  });

  // ── modelForRole("quality") — fallback (line 66) ────────────────────────────

  test("modelForRole quality returns doc id when in catalog", async () => {
    writeTestDoc({ roles: { quality: { id: "qual-model" } } });
    mockListSwapModels([{ id: "qual-model" }]);
    expect(await modelForRole("quality")).toBe("qual-model");
  });

  test("modelForRole quality falls back to hardcoded (line 66)", async () => {
    writeTestDoc({ roles: { quality: { id: "not-in-catalog" } } });
    mockListSwapModels([{ id: "other-model" }]);
    expect(await modelForRole("quality")).toBe("beellama/qwen-flash-64k");
  });

  // ── listSwapModels error paths (via pickDefaultModel) ────────────────────────

  test("modelForRole default handles fetch HTTP error", async () => {
    writeTestDoc({});
    mockListSwapFail(503);
    const result = await modelForRole("default");
    // Falls through pickDefaultModel → listSwapModels fails → returns preferred default
    expect(result).toBe("beellama/qwen-flash-64k");
  });

  test("modelForRole default handles fetch network error", async () => {
    writeTestDoc({});
    mockListSwapError("ECONNREFUSED");
    const result = await modelForRole("default");
    expect(result).toBe("beellama/qwen-flash-64k");
  });

  // ── validateBestModelsAgainstCatalog (lines 70-83) ──────────────────────────

  test("validateBestModelsAgainstCatalog returns no_doc when missing (line 74)", async () => {
    rmSync(REAL_PATH, { force: true });
    mockListSwapModels([]);
    const r = await validateBestModelsAgainstCatalog(REAL_PATH);
    expect(r.ok).toBe(false);
    expect(r.missing).toEqual(["no_doc"]);
    expect(r.doc).toBeNull();
  });

  test("validateBestModelsAgainstCatalog detects missing models (lines 78-81)", async () => {
    writeTestDoc({
      roles: { fast: { id: "missing-model" }, quality: { id: "exists" } },
    });
    mockListSwapModels([{ id: "exists" }]);
    const r = await validateBestModelsAgainstCatalog(REAL_PATH);
    expect(r.ok).toBe(false);
    expect(r.missing).toContain("fast:missing-model");
  });

  test("validateBestModelsAgainstCatalog ok when all present", async () => {
    writeTestDoc({
      roles: {
        fast: { id: "a" },
        quality: { id: "b" },
        longctx: { id: "c" },
      },
    });
    mockListSwapModels([{ id: "a" }, { id: "b" }, { id: "c" }]);
    const r = await validateBestModelsAgainstCatalog(REAL_PATH);
    expect(r.ok).toBe(true);
    expect(r.missing).toEqual([]);
  });

  // ── watchBestModelsSse (lines 89-108) ───────────────────────────────────────

  test("watchBestModelsSse creates .state dir and returns abort (lines 89-108)", () => {
    // watchBestModelsSse calls watchSwapModelsSseRefresh which calls
    // watchSwapModelsSse which does fetch — mock it to not connect
    mockFetch.mockResolvedValue({
      ok: false,
      body: null,
    });
    const h = watchBestModelsSse(REAL_PATH);
    expect(typeof h.abort).toBe("function");
    // Verify .state dir was created
    expect(existsSync(join(SOV, ".state"))).toBe(true);
    h.abort();
  });

  test("watchBestModelsSse abort stops gracefully", () => {
    mockFetch.mockResolvedValue({
      ok: false,
      body: null,
    });
    const h = watchBestModelsSse(REAL_PATH);
    h.abort();
    // Double-abort should be safe
    h.abort();
  });

  test("watchBestModelsSse callback writes beat file on SSE event (lines 94-108)", async () => {
    // Create a real best-models doc for the callback to validate
    writeTestDoc({ roles: { fast: { id: "fast-model" } } });

    const encoder = new TextEncoder();
    const sseData = 'data: {"model":"m1","event":"loaded"}\n\n';
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode(sseData));
        setTimeout(() => controller.close(), 100);
      },
    });
    mockFetch.mockResolvedValue({ ok: true, body: stream });

    const h = watchBestModelsSse(REAL_PATH);

    // Wait for: SSE read + 1500ms debounce (default) + margin
    // Use shorter timeout by watching for beat file creation
    const beatPath = join(SOV, ".state/best-models-sse-beat.json");
    let beatWritten = false;
    for (let i = 0; i < 80; i++) {
      await new Promise((r) => setTimeout(r, 100));
      if (existsSync(beatPath)) {
        beatWritten = true;
        break;
      }
    }
    h.abort();

    expect(beatWritten).toBe(true);
    // Verify beat file content
    const beat = JSON.parse(readFileSync(beatPath, "utf8"));
    expect(beat.ts).toBeTruthy();
    expect(typeof beat.ok).toBe("boolean");
  });
});
