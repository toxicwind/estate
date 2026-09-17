export type ModelTag = "codex";

export type ClaudeSeries = "opus" | "sonnet" | "haiku";

export type ModelIdentity = {
  rawId: string;
  family?: "gpt-5" | "claude";
  version?: {
    major: number;
    minor?: number;
  };
  series?: ClaudeSeries;
  tags: Set<ModelTag>;
};

const GPT_ID_PATTERN = /^gpt-(\d+)(?:\.(\d+))?(?:-(.+))?$/;
const CLAUDE_SERIES_PATTERN = /\b(opus|sonnet|haiku)\b/;

export function inspectModelIdentity(modelId?: string): ModelIdentity | undefined {
  if (!modelId) return undefined;

  const rawId = modelId.trim().toLowerCase();
  if (!rawId) return undefined;

  const gptMatch = rawId.match(GPT_ID_PATTERN);
  if (gptMatch) {
    const major = Number(gptMatch[1]);
    const minor = gptMatch[2] ? Number(gptMatch[2]) : undefined;
    const suffix = gptMatch[3];
    const tags = new Set<ModelTag>();

    for (const token of suffix?.split("-") ?? []) {
      if (token === "codex") {
        tags.add("codex");
      }
    }

    return {
      rawId,
      family: major === 5 ? "gpt-5" : undefined,
      version: { major, minor },
      tags,
    };
  }

  const claudeMatch = rawId.match(CLAUDE_SERIES_PATTERN);
  if (claudeMatch) {
    return {
      rawId,
      family: "claude",
      series: claudeMatch[1] as ClaudeSeries,
      tags: new Set<ModelTag>(),
    };
  }

  return { rawId, tags: new Set<ModelTag>() };
}
