import type { PromptLayer } from "../../../prompt.js";
import { joinSections, section } from "../../../prompt.js";

export const GPT5_FAMILY_LAYER: PromptLayer = {
  marker: "## OpenAI GPT-5 Family Base (Pi)",
  content: joinSections(
    section("follow_through_policy", [
      "If the user's intent is clear and the next step is reversible and low-risk, proceed without asking. Ask only when the next step is irreversible, affects shared state, or requires a choice that would materially change the outcome.",
      "When proceeding on assumption, state what you assumed in one sentence.",
    ]),
    section("response_openers", [
      "Do not begin responses with conversational interjections, acknowledgements, or framing phrases.",
    ]),
  ),
  meta: {
    target: "gpt-5-family",
    purpose: "correction",
    fixes: [
      "excessive confirmation-seeking on reversible low-risk actions",
      "chatty or meta-commentary-heavy response openers",
    ],
    nonGoals: [
      "do not restate harness-core scope, grounding, or verbosity rules",
      "do not encode model-exact quirks that belong in version layers",
    ],
  },
};
