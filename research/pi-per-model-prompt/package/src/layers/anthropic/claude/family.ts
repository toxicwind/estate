import type { PromptLayer } from "../../../prompt.js";
import { joinSections, section } from "../../../prompt.js";

export const CLAUDE_FAMILY_LAYER: PromptLayer = {
  marker: "## Anthropic Claude Family Base (Pi)",
  content: joinSections(
    section("xml_structure_preference", [
      "Use XML tags to delineate structured input/output regions when the prompt does not specify a format.",
      "Keep XML structure flat and readable; avoid unnecessary nesting.",
    ]),
    section("long_context_attention", [
      "When citing information from context, provide pinpoint references (file path, line number, section name).",
      "Attend to middle and late sections of long context as carefully as early ones.",
      "When context contains contradictory information, flag the conflict and state which source you follow and why.",
    ]),
  ),
  meta: {
    target: "claude-family",
    purpose: "correction",
    fixes: [
      "positional attention bias in long-context processing",
    ],
    nonGoals: [
      "do not restate harness-core rules — those apply to every model",
      "do not encode series-specific quirks that belong in future per-series layers",
    ],
  },
};
