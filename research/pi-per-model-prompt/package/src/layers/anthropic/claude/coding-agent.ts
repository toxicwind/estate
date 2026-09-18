import type { PromptLayer } from "../../../prompt.js";
import { joinSections, section } from "../../../prompt.js";

export const CLAUDE_CODING_AGENT_LAYER: PromptLayer = {
  marker: "## Anthropic Claude Coding Agent (Pi)",
  content: joinSections(
    section("comment_discipline", [
      "Default to writing no comments. Only add one when the WHY is non-obvious: a hidden constraint, a subtle invariant, a workaround for a specific bug.",
      "Do not explain WHAT the code does — well-named identifiers already do that. Do not reference the current task or callers in comments; those belong in the commit message.",
      "Do not remove existing comments unless you are removing the code they describe or you know they are wrong.",
    ]),
    section("implementation_reporting", [
      "For implementation tasks, the final response should cover: What changed, Where, Verified, and Risks or Notes. If verification was not run, say so.",
    ]),
  ),
  meta: {
    target: "claude-coding-agent",
    purpose: "correction",
    fixes: [
      "over-commenting: Claude adds comments explaining what code does or references the current task",
      "incomplete or missing implementation summaries",
    ],
    nonGoals: [
      "do not restate harness-core rules — those apply to every model",
    ],
  },
};
