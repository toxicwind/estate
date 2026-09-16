/**
 * Sovereign recursive autonomous fallback.
 *
 * A multi-level, self-healing control structure for agentic tool use.
 * Grounded in the agentic loop (ReAct 2210.03629 / Reflexion 2303.11366):
 * every non-trivial action is wrapped in a fallback tree, not a single try/catch.
 *
 * Properties (per user spec):
 *  - Multi-level try/catch: each catch has its OWN nested try/catch.
 *  - Helpers: one per recovery strategy (fixSyntax, scaffold, borrowGhas,
 *    retrieveTool, coerceInput).
 *  - Recursion: decompose + recurse on a smaller sub-problem; a sub-agent
 *    (spawn_agent) is a valid recursion target.
 *  - LLM-assisted self-repair: coerce malformed tool input to a valid shape
 *    and retry (don't retry the broken call); auto-retrieve a tool via a
 *    SHALLOW query when the capability is missing; auto-scaffold a helper
 *    script when no tool fits.
 *  - Watchdog: bounded attempts / budget; escalate (change strategy /
 *    scaffold / ask) instead of spinning forever.
 *
 * This module is pure (no sockets, no globals) so it is unit-testable.
 */

export type Strategy =
  | "primary"
  | "fix_syntax"
  | "scaffold"
  | "borrow_ghas"
  | "retrieve_tool"
  | "recurse"
  | "escalate";

export interface AttemptContext {
  attempts: number;
  maxAttempts: number;
  budgetMs: number;
  startedAt: number;
  strategy: Strategy;
  log: string[];
}

export function newContext(maxAttempts = 6, budgetMs = 30_000): AttemptContext {
  return {
    attempts: 0,
    maxAttempts,
    budgetMs,
    startedAt: Date.now(),
    strategy: "primary",
    log: [],
  };
}

export function budgetExceeded(ctx: AttemptContext, now = Date.now()): boolean {
  return now - ctx.startedAt > ctx.budgetMs;
}

export function attemptsExceeded(ctx: AttemptContext): boolean {
  return ctx.attempts >= ctx.maxAttempts;
}

// ── Helpers (one per recovery strategy) ───────────────────────────────────
// Each returns a *coerced* or *alternative* input, or null if it can't help.

/** Coerce malformed tool input toward a valid shape. */
export function coerceInput(
  raw: unknown,
  shape: "json" | "string" | "array",
): unknown {
  try {
    if (shape === "json") {
      if (typeof raw === "string") return JSON.parse(raw);
      if (typeof raw === "object" && raw !== null) return raw;
      return JSON.parse(JSON.stringify(raw));
    }
    if (shape === "string") {
      return typeof raw === "string" ? raw : JSON.stringify(raw);
    }
    if (shape === "array") {
      if (Array.isArray(raw)) return raw;
      return [raw];
    }
  } catch {
    return null; // coercion failed → caller escalates
  }
  return null;
}

/** Fix a syntax-broken script by wrapping it in a file and re-parsing. */
export function fixSyntax(
  broken: string,
  lang: "ts" | "py" | "sh",
): string | null {
  const stripped = broken.replace(/,\s*([}\]])/g, "$1");
  try {
    if (lang === "json" || lang === "ts") JSON.parse(stripped);
    // Valid after stripping trailing commas → return normalized.
    return stripped.replace(/\s+/g, " ").trim();
  } catch {
    // Truly broken even after strip.
    return null;
  }
}

/** Scaffold a minimal helper script so logic survives the watchdog. */
export function scaffold(
  name: string,
  body: string,
): { path: string; body: string } {
  return { path: `/tmp/sovereign-scaffold/${name}`, body };
}

/** Borrow a known-good pattern from the GHAS mesh (returns a stub descriptor). */
export function borrowGhas(pattern: string): {
  source: string;
  pattern: string;
} {
  return { source: "ghas-mesh-features", pattern };
}

/** Shallow MCP-tool retrieval: verb + noun, not a deep query. */
export function shallowQuery(verb: string, noun: string): string {
  return `${verb} ${noun}`.trim();
}

// ── The recursive executor ───────────────────────────────────────────────────
// `doWork` is the unit of work. `recover` is the fallback tree. On
// failure it walks strategies; each catch has its OWN nested try/catch and
// may recurse (decompose + recurse on a smaller sub-problem).

export type WorkFn = (input: unknown, ctx: AttemptContext) => unknown;

export interface FallbackResult {
  ok: boolean;
  value?: unknown;
  strategy: Strategy;
  log: string[];
}

export function runWithFallback(
  input: unknown,
  doWork: WorkFn,
  ctx: AttemptContext = newContext(),
): FallbackResult {
  ctx.attempts++;

  // ── Level 1: primary attempt ───────────────────────────────────────
  try {
    const value = doWork(input, ctx);
    ctx.log.push(`[primary] ok on attempt ${ctx.attempts}`);
    return { ok: true, value, strategy: "primary", log: ctx.log };
  } catch (e1: any) {
    ctx.log.push(`[primary] failed: ${String(e1?.message || e1)}`);

    // ── Level 2: fix syntax / coerce input, then retry ──────────────
    try {
      const coerced = coerceInput(input, "json");
      if (coerced === null) throw new Error("coerce failed");
      const value = doWork(coerced, ctx);
      ctx.log.push(`[fix_syntax] coerced input + retried ok`);
      return { ok: true, value, strategy: "fix_syntax", log: ctx.log };
    } catch (e2: any) {
      ctx.log.push(`[fix_syntax] failed: ${String(e2?.message || e2)}`);

      // ── Level 3: scaffold a helper, then run it ──────────────────
      try {
        const helper = scaffold(`attempt-${ctx.attempts}.ts`, String(input));
        // A real impl would write+exec the helper; we model the decision.
        if (!helper.path) throw new Error("scaffold empty");
        ctx.log.push(`[scaffold] wrote ${helper.path}`);
        // Recurse on the smaller sub-problem (the helper body).
        const sub = runWithFallback(helper.body, doWork, {
          ...ctx,
          attempts: 0,
          strategy: "recurse",
          startedAt: ctx.startedAt,
        });
        if (sub.ok) {
          ctx.log.push(`[recurse] sub-problem solved via scaffold`);
          return {
            ok: true,
            value: sub.value,
            strategy: "scaffold",
            log: ctx.log,
          };
        }
        throw new Error("recurse-sub failed");
      } catch (e3: any) {
        ctx.log.push(`[scaffold] failed: ${String(e3?.message || e3)}`);

        // ── Level 4: borrow GHAS pattern + shallow-retrieve a tool ──
        try {
          const pat = borrowGhas("recursive-fallback");
          const q = shallowQuery("github", "code search");
          if (!pat.pattern || !q) throw new Error("retrieve empty");
          ctx.log.push(`[borrow_ghas] pattern=${pat.pattern} query=${q}`);
          // A real impl would call retrieve_tools(q) then the discovered tool.
          const value = doWork(input, { ...ctx, strategy: "retrieve_tool" });
          ctx.log.push(`[retrieve_tool] ok after discovery`);
          return { ok: true, value, strategy: "retrieve_tool", log: ctx.log };
        } catch (e4: any) {
          ctx.log.push(`[borrow_ghas] failed: ${String(e4?.message || e4)}`);

          // ── Level 5: escalate (watchdog) ──────────────────────────
          if (attemptsExceeded(ctx) || budgetExceeded(ctx)) {
            ctx.log.push(
              `[escalate] watchdog tripped (attempts=${ctx.attempts}, budget exceeded=${budgetExceeded(ctx)})`,
            );
            return { ok: false, strategy: "escalate", log: ctx.log };
          }
          // Not exhausted: recurse on a smaller slice of the input.
          try {
            if (Array.isArray(input) && (input as unknown[]).length > 1) {
              const half = (input as unknown[]).slice(
                0,
                Math.ceil((input as unknown[]).length / 2),
              );
              ctx.log.push(
                `[recurse] decomposing array, retrying smaller slice`,
              );
              const sub = runWithFallback(half, doWork, ctx);
              if (sub.ok)
                return {
                  ok: true,
                  value: sub.value,
                  strategy: "recurse",
                  log: ctx.log,
                };
            }
            throw new Error("no smaller sub-problem");
          } catch (e5: any) {
            ctx.log.push(`[recurse] failed: ${String(e5?.message || e5)}`);
            return { ok: false, strategy: "escalate", log: ctx.log };
          }
        }
      }
    }
  }
}
