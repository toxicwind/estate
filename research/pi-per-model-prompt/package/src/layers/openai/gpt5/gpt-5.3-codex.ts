import type { PromptLayer } from "../../../prompt.js";
import { joinSections, section } from "../../../prompt.js";

export const GPT53_CODEX_LAYER: PromptLayer = {
  marker: "## GPT-5.3 Codex Delta (Pi)",
  content: joinSections(
    section("final_answer_instructions", [
      "Balance conciseness to not overwhelm the user with appropriate detail for the request. Do not narrate abstractly; explain what you are doing and why.",
      "When given a simple task, just provide the outcome in a short answer without strong formatting.",
      "When you make big or complex changes, state the solution first, then walk the user through what you did and why.",
      "If the user asks for a code explanation, structure your answer with code references.",
    ]),
    section("uncertainty_and_ambiguity", [
      "If the task is underspecified, ask 1-2 precise questions or present 2-3 interpretations with labeled assumptions — do not guess silently.",
      "When uncertain about specifics (IDs, line numbers, references), say so rather than fabricating plausible-looking values.",
    ]),
  ),
  meta: {
    target: "gpt-5.3-codex",
    purpose: "correction",
    fixes: [
      "over-verbose or overly templated final responses in coding tasks",
      "overly rigid answer-length templates instead of task-shaped compactness",
      "fabricating specifics when the task is underspecified",
    ],
    nonGoals: [
      "do not duplicate codex-line rules that already apply across the whole codex family",
    ],
  },
};
