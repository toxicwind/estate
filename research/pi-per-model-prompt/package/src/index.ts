import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { applyLayers } from "./prompt.js";
import { resolveLayers } from "./resolve.js";

export default function perModelPrompt(pi: ExtensionAPI): void {
  pi.on("before_agent_start", async (event, ctx) => {
    const layers = resolveLayers(ctx);
    if (layers.length === 0) {
      return undefined;
    }

    const systemPrompt = applyLayers(event.systemPrompt, layers);
    if (systemPrompt === event.systemPrompt) {
      return undefined;
    }

    return { systemPrompt };
  });

  pi.on("before_provider_request", (event, ctx) => {
    if (ctx.model?.id?.trim().toLowerCase() !== "gpt-5.4") {
      return undefined;
    }

    if (
      ctx.model.api
      && ctx.model.api !== "openai-responses"
      && ctx.model.api !== "openai-codex-responses"
      && ctx.model.api !== "azure-openai-responses"
    ) {
      return undefined;
    }

    const payload = event.payload;
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
      return undefined;
    }

    const payloadRecord = payload as Record<string, unknown>;
    if (!("model" in payloadRecord) || !("input" in payloadRecord)) {
      return undefined;
    }

    if (typeof payloadRecord.model !== "string") {
      return undefined;
    }

    const text = payloadRecord.text;
    if (
      text !== undefined
      && (typeof text !== "object" || text === null || Array.isArray(text))
    ) {
      return undefined;
    }

    return {
      ...payloadRecord,
      text: {
        ...((text as Record<string, unknown> | undefined) ?? {}),
        verbosity: "low",
      },
    };
  });
}
