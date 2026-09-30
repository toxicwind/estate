import type { Model } from "./types";

// Canonical capability key -> human label. Shared by the model Details tab
// and the Models list so labels live in exactly one place.
export const capabilityLabels: Record<string, string> = {
  vision: "Vision",
  audio_transcriptions: "Transcription",
  audio_speech: "Speech",
  image_generation: "Image Gen",
  image_to_image: "Img→Img",
  function_calling: "Function Calling",
  reranker: "Reranker",
};

// Where a capability badge came from. The herd API merges config-set and
// auto-discovered capabilities field-by-field without exposing per-field
// provenance, so badges sourced from /v1/models or the modelStatus feed
// default to "discovered": the discovery pipeline is what populates them on
// this estate (herd.yaml carries no capability blocks today). An explicit
// model.capabilitySources entry overrides the default wherever provenance
// is actually known.
export type CapabilitySource = "discovered" | "configured" | "unknown";

export interface CapabilityBadge {
  key: string;
  label: string;
  source?: CapabilitySource;
}

// Tooltip text per provenance, shown on the badge title attribute.
export const capabilitySourceLabels: Record<CapabilitySource, string> = {
  discovered: "Auto-discovered by herd\u2019s capability probe when the model became ready",
  configured: "Set explicitly in herd.yaml (capabilities block)",
  unknown: "Capability source not reported by this herd version",
};

// Extra badge classes per provenance. Discovered badges get a dashed outline
// in the badge's own tint so probe results are separable from hand-set
// values at a glance; configured badges keep the plain pastel fill.
export const capabilitySourceBadgeClass: Record<CapabilitySource, string> = {
  discovered: "border border-dashed border-current",
  configured: "",
  unknown: "opacity-75",
};

// The model fields badge helpers read. A single alias keeps the helpers and
// their callers on the same shape.
export type BadgeModel = Pick<Model, "capabilities" | "context_length" | "capabilitySources">;

// Resolves a badge's provenance: an explicit per-model override wins, then
// the caller-supplied default (used for badges sourced from the herd API),
// otherwise undefined so callers render the neutral style.
export function resolveCapabilitySource(
  model: BadgeModel,
  key: string,
  defaultSource?: CapabilitySource,
): CapabilitySource | undefined {
  const explicit = model.capabilitySources?.[key];
  if (explicit) return explicit;
  return defaultSource;
}

// Formats a token count as a compact context-window badge. Uses decimal units
// (128000 -> "128K", 1000000 -> "1M") to match the conventional "128K context"
// wording used by llama.cpp and OpenAI-compatible listings.
export function formatContextLength(tokens: number): string {
  if (tokens <= 0) return "";
  if (tokens >= 1_000_000) {
    const m = tokens / 1_000_000;
    return Number.isInteger(m) ? `${m}M` : `${m.toFixed(1)}M`;
  }
  if (tokens >= 1_000) {
    const k = tokens / 1_000;
    return Number.isInteger(k) ? `${k}K` : `${Math.round(k)}K`;
  }
  return String(tokens);
}

// Muted pastel background/text classes per capability badge key, so each is
// visually distinct on the Models list. Low-opacity backgrounds keep the look
// soft; the 700/300 text shades keep contrast in light and dark mode.
export const capabilityBadgeClass: Record<string, string> = {
  vision: "bg-violet-500/15 text-violet-700 dark:text-violet-300",
  audio_transcriptions: "bg-amber-500/15 text-amber-700 dark:text-amber-300",
  audio_speech: "bg-rose-500/15 text-rose-700 dark:text-rose-300",
  image_generation: "bg-fuchsia-500/15 text-fuchsia-700 dark:text-fuchsia-300",
  image_to_image: "bg-orange-500/15 text-orange-700 dark:text-orange-300",
  function_calling: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300",
  reranker: "bg-indigo-500/15 text-indigo-700 dark:text-indigo-300",
  context: "bg-sky-500/15 text-sky-700 dark:text-sky-300",
};

export interface ListCapabilityBadgesOptions {
  // Provenance stamped onto every badge that has no explicit
  // model.capabilitySources entry. The Models dashboard passes "discovered"
  // for badges sourced from the herd API.
  defaultSource?: CapabilitySource;
}

// Returns the capability badges for a Models list row: every reported
// capability in canonical order (mirroring the Details tab tag set), with the
// context window last so it sits on the right of the group. Badges are
// reactive to the modelStatus feed: the feed carries the merged
// config+discovered capabilities, so each feed update re-derives this list.
export function listCapabilityBadges(
  model: BadgeModel,
  opts?: ListCapabilityBadgesOptions,
): CapabilityBadge[] {
  const badges: CapabilityBadge[] = [];

  const caps = model.capabilities ?? {};
  for (const key of Object.keys(capabilityLabels)) {
    if (caps[key as keyof Model["capabilities"]]) {
      badges.push({
        key,
        label: capabilityLabels[key],
        source: resolveCapabilitySource(model, key, opts?.defaultSource),
      });
    }
  }

  const ctx = model.context_length ?? 0;
  if (ctx > 0) {
    badges.push({
      key: "context",
      label: formatContextLength(ctx),
      source: resolveCapabilitySource(model, "context", opts?.defaultSource),
    });
  }

  return badges;
}

// Push-first merge of a modelStatus feed entry with its /v1/models record.
//
// The feed now carries capabilities, context_length and capabilitySources
// the instant herd learns them (ModelCapabilitiesChangedEvent pushed over
// SSE), so a feed payload with any enabled capability wins: badges render
// with no round-trip. When the feed entry has no capability payload yet, the
// debounced /v1/models refetch (refreshPlaygroundModels) supplies the data
// as the fallback. `modalities` has no feed field, so it always comes from
// the /v1/models record.
export function mergeFeedCapabilities(feedModel: Model, apiModel?: Model): Model {
  const feedHasCaps = Object.values(feedModel.capabilities ?? {}).some(Boolean);
  if (!apiModel || feedHasCaps) {
    return {
      ...feedModel,
      modalities: apiModel?.modalities ?? feedModel.modalities,
    };
  }
  return {
    ...feedModel,
    capabilities: apiModel.capabilities,
    context_length: apiModel.context_length ?? feedModel.context_length,
    modalities: apiModel.modalities ?? feedModel.modalities,
    capabilitySources: apiModel.capabilitySources,
  };
}
