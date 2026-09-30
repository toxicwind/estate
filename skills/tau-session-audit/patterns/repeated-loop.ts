// Pattern: Repeated Command Failure Loop
// Detects models repeating the exact same failing command or error 3+ times without adapting.

import type { PatternDetector, PatternMatch, SessionContext, SessionEvent } from "./types";

export const repeatedLoopDetector: PatternDetector = {
  id: "repeated-loop",
  name: "Repeated Command Failure Loop",
  description:
    "Detects sessions where the model repeats failing commands or hits the exact same error multiple times without diagnosing the underlying cause.",

  detect(events: SessionEvent[], context?: SessionContext): PatternMatch[] {
    const matches: PatternMatch[] = [];
    let currentModel = context?.model || "unknown";

    const errorCounts = new Map<string, { count: number; firstIndex: number; model: string }>();

    for (let i = 0; i < events.length; i++) {
      const e = events[i];

      if (e.type === "model_change" && typeof e.model === "string") {
        currentModel = e.model;
      }

      if (e.type === "message" && e.message?.role === "toolResult") {
        const isError = Boolean(e.message.isError);
        const contentStr = String(e.message.content || "");

        if (isError || contentStr.includes("error TS") || contentStr.includes("Cannot read file") || contentStr.includes("rule_violation")) {
          // Normalize error snippet key (first 80 chars)
          const key = contentStr.replace(/\s+/g, " ").slice(0, 80);
          const existing = errorCounts.get(key) || { count: 0, firstIndex: i, model: currentModel };
          existing.count++;
          errorCounts.set(key, existing);
        }
      }
    }

    for (const [key, data] of errorCounts.entries()) {
      if (data.count >= 3) {
        matches.push({
          patternId: "REPEATED_COMMAND_LOOP",
          name: "Repeated Tool Failure Loop",
          severity: data.count >= 5 ? "critical" : "high",
          description: `Model ${data.model} hit the same error ${data.count} times without adapting.`,
          details: {
            eventIndex: data.firstIndex,
            model: data.model,
            repeatCount: data.count,
            errorSnippet: key,
          },
        });
      }
    }

    return matches;
  },
};
