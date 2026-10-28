/**
 * thinking-auto-shim — shim OFF tau's per-turn `auto` thinking classifier.
 *
 * tau's `auto` thinking level (modelRoles `:auto` / `/thinking auto`) resolves
 * each turn by running a JUDGE model call (classifyDifficulty in
 * coding-agent/src/auto-thinking/classifier.ts) that picks low..xhigh for the
 * prompt, then applies the classified effort. That costs one extra model round
 * trip per turn (4s abort budget) and makes effort/price/latency vary per turn.
 *
 * This extension replaces `auto` with a FIXED concrete thinking level before
 * each turn starts. Setting a concrete level clears the session's auto flag in
 * ModelControls (`#autoThinking = false`), so `applyAutoThinkingLevel` skips
 * the classifier entirely — no judge call, deterministic effort.
 *
 * Config:
 *   TAU_AUTO_THINK_SHIM_LEVEL = off | min | low | medium | high | xhigh | max
 *   (default "low"). Set to "off" to fully disable reasoning.
 *
 * `ultrathink` magic keyword still works: the classifier bypass path in
 * model-controls applies only when `#autoThinking` is set, so an explicit
 * ultrathink WILL be lost while the shim is active — that's the price of
 * shimming auto off; mention it in the session if you need both.
 */
import type { ExtensionAPI, ExtensionContext } from "tau";

const LEVELS = ["off", "min", "low", "medium", "high", "xhigh", "max"] as const;
type Level = (typeof LEVELS)[number];

function normalizeLevel(raw: string | undefined): Level {
  const v = (raw ?? "low").trim().toLowerCase();
  return (LEVELS as readonly string[]).includes(v) ? (v as Level) : "low";
}

const FIXED_LEVEL: Level = normalizeLevel(process.env.TAU_AUTO_THINK_SHIM_LEVEL);
const AUTO = "auto" as const;

export default function thinkingAutoShim(pi: ExtensionAPI): void {
  const shim = (_event: unknown, ctx: ExtensionContext): void => {
    try {
      const current = ctx.getThinkingLevel();
      if (current === AUTO) {
        ctx.setThinkingLevel(FIXED_LEVEL);
        ctx.ui?.notify?.(`[thinking-auto-shim] auto → ${FIXED_LEVEL}`, "info");
      }
    } catch {
      // Non-fatal: never break a turn because the shim misbehaved.
    }
  };

  // session_start covers role/model switches that re-apply `:auto`; 
  // before_agent_start covers every turn so a mid-session auto re-engage
  // (e.g. /thinking auto) is re-shimmed before the classifier would run.
  pi.on("session_start", shim as never);
  pi.on("before_agent_start", shim as never);
}