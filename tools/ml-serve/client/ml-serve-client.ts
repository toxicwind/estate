/**
 * ml-serve client — dependency-free Bun/TypeScript client for the resident
 * ML inference daemon (tools/ml-serve/server.py).
 *
 * Zero npm dependencies: plain `fetch` only. Drop this file straight into
 * any Bun tree (e.g. the quickshell wallpaper picker) and import it:
 *
 *   import { mlServe } from "./ml-serve-client";
 *   const best = await mlServe.pick("/home/toxic/Pictures/Wallpapers");
 *   if (best.best) console.log(best.best.path, best.best.score);
 *
 * Tags come from e621's native tagging (md5 lookup, daemon-side cached) —
 * there is no local tagger. The daemon must be running
 * (default http://127.0.0.1:25180). See ../README.md for the daemon side.
 */

export interface SegmentResult {
  path: string;
  /** [x0, y0, x1, y1] in original image pixels, or null when no subject. */
  bbox: [number, number, number, number] | null;
  /** [cx, cy] in original image pixels, or null when no subject. */
  centroid: [number, number] | null;
  /** Fraction of pixels covered by the subject mask. */
  coverage: number;
  ms: number;
  provider: string;
}

export interface LookupResult {
  path: string;
  md5: string;
  /** Native e621 tags, or null when the file is not on e621. */
  tag_string: string[] | null;
  source: "e621" | "miss" | "error";
  ms: number;
}

export interface PickBest {
  path: string;
  /** Lower is better: aspect_term + upscale − boost·furry·male − penalty·watermark. */
  score: number;
  furry: 0 | 1;
  male: 0 | 1;
  watermark: 0 | 1;
  tag_source: "e621" | "miss" | "error";
  matched_tags: string[];
  tag_count: number;
}

export interface PickResult {
  best: PickBest | null;
  candidates: number;
  ms: number;
}

export interface PickOptions {
  furry_boost?: number;
  wm_penalty?: number;
  /** Target width/height ratio for the aspect term (omit = aspect-agnostic). */
  target_aspect?: number;
}

export interface ModelStat {
  loaded: boolean;
  provider?: string;
  load_ms?: number;
  inferences?: number;
  avg_ms?: number;
}

export interface HealthResult {
  ok: boolean;
  providers_available: string[];
  provider_preference: string[];
  models: Record<string, ModelStat>;
  tag_source: string;
  e621: {
    lookups: number;
    hits: number;
    misses: number;
    errors: number;
    cached: number;
  };
  pool: string;
  pool_cached: number;
  cache_interval_s: number;
}

export class MlServeError extends Error {
  readonly status: number;
  constructor(status: number, message: string) {
    super(`ml-serve ${status}: ${message}`);
    this.name = "MlServeError";
    this.status = status;
  }
}

export class MlServeClient {
  readonly baseUrl: string;

  constructor(baseUrl = "http://127.0.0.1:25180") {
    this.baseUrl = baseUrl.replace(/\/+$/, "");
  }

  private async post<T>(route: string, body: unknown): Promise<T> {
    const res = await fetch(`${this.baseUrl}${route}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = (await res.json()) as Record<string, unknown>;
    if (!res.ok) {
      throw new MlServeError(res.status, String(data.error ?? "unknown error"));
    }
    return data as T;
  }

  /** Daemon liveness + loaded models + e621 cache stats + timings. */
  async health(): Promise<HealthResult> {
    const res = await fetch(`${this.baseUrl}/health`);
    if (!res.ok) throw new MlServeError(res.status, "health check failed");
    return (await res.json()) as HealthResult;
  }

  /** Block until the daemon answers /health (or timeout). */
  async waitReady(timeoutMs = 30_000): Promise<void> {
    const deadline = Date.now() + timeoutMs;
    for (;;) {
      try {
        const h = await this.health();
        if (h.ok) return;
      } catch {
        /* not up yet */
      }
      if (Date.now() >= deadline) {
        throw new MlServeError(0, `daemon not ready at ${this.baseUrl}`);
      }
      await new Promise((r) => setTimeout(r, 500));
    }
  }

  /**
   * Resolve a file's native e621 tags by md5 (daemon-side cached).
   * `tag_string` is null when the file is not on e621.
   */
  lookup(path: string): Promise<LookupResult> {
    return this.post<LookupResult>("/lookup", { path });
  }

  /** Anime subject segmentation → bbox/centroid/coverage in original px. */
  segment(path: string): Promise<SegmentResult> {
    return this.post<SegmentResult>("/segment", { path });
  }

  /**
   * Rank every image in `dir` on cached e621 native tags and return the
   * best pick. Lower score wins; the furry/male boost pushes furry-male-
   * tagged art to the top. Files missing from e621 score on geometry alone.
   */
  pick(dir: string, opts: PickOptions = {}): Promise<PickResult> {
    return this.post<PickResult>("/pick", { dir, ...opts });
  }

  /**
   * Convenience: 1 when the native tag list hits both a furry-ish tag
   * (anthro/kemono/…) and a male tag, else 0.
   */
  static furryMaleScore(
    tags: string[] | null,
    furryTags = ["anthro", "kemono"],
    maleTags = ["male"],
  ): 0 | 1 {
    if (!tags) return 0;
    const set = new Set(tags);
    const furry = furryTags.some((t) => set.has(t));
    const male = maleTags.some((t) => set.has(t));
    return furry && male ? 1 : 0;
  }
}

/** Default client pointed at the standard daemon address. */
export const mlServe = new MlServeClient();
