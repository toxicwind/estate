import type { ExtensionContext } from "@mariozechner/pi-coding-agent";
import type { PromptLayer } from "./prompt.js";
import { inspectModelIdentity } from "./model-identity.js";
import { HARNESS_CORE_LAYER } from "./layers/base.js";
import { GPT54_LAYER } from "./layers/openai/gpt5/gpt-5.4.js";
import { GPT53_CODEX_LAYER } from "./layers/openai/gpt5/gpt-5.3-codex.js";
import { GPT5_FAMILY_LAYER } from "./layers/openai/gpt5/family.js";
import { CLAUDE_FAMILY_LAYER } from "./layers/anthropic/claude/family.js";
import { CLAUDE_CODING_AGENT_LAYER } from "./layers/anthropic/claude/coding-agent.js";

export type ModelContext = Pick<ExtensionContext, "model">;

export function resolveLayersForModelId(modelId?: string): PromptLayer[] {
  const layers: PromptLayer[] = [HARNESS_CORE_LAYER];
  const identity = inspectModelIdentity(modelId);
  if (!identity) return layers;

  if (identity.family === "gpt-5") {
    layers.push(GPT5_FAMILY_LAYER);

    if (identity.version?.major === 5 && identity.version.minor === 4) {
      layers.push(GPT54_LAYER);
    }

    if (
      identity.version?.major === 5
      && identity.version.minor === 3
      && identity.tags.has("codex")
    ) {
      layers.push(GPT53_CODEX_LAYER);
    }

    return layers;
  }

  if (identity.family === "claude") {
    layers.push(CLAUDE_FAMILY_LAYER, CLAUDE_CODING_AGENT_LAYER);
    return layers;
  }

  return layers;
}

export function resolveLayers(ctx: ModelContext): PromptLayer[] {
  return resolveLayersForModelId(ctx.model?.id);
}
