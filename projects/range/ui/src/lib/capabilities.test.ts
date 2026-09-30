import { describe, it, expect } from "vitest";
import {
  formatContextLength,
  listCapabilityBadges,
  capabilityLabels,
  capabilityBadgeClass,
  capabilitySourceLabels,
  capabilitySourceBadgeClass,
  resolveCapabilitySource,
} from "./capabilities";
import type { Model } from "./types";

describe("formatContextLength", () => {
  it("returns empty for zero or negative", () => {
    expect(formatContextLength(0)).toBe("");
    expect(formatContextLength(-1)).toBe("");
  });

  it("passes small values through as-is", () => {
    expect(formatContextLength(512)).toBe("512");
    expect(formatContextLength(999)).toBe("999");
  });

  it("formats thousands with a K suffix", () => {
    expect(formatContextLength(1000)).toBe("1K");
    expect(formatContextLength(8192)).toBe("8K");
    expect(formatContextLength(128000)).toBe("128K");
    expect(formatContextLength(200000)).toBe("200K");
  });

  it("rounds non-round thousands to the nearest K", () => {
    expect(formatContextLength(32768)).toBe("33K");
    expect(formatContextLength(131072)).toBe("131K");
  });

  it("formats whole millions with an M suffix", () => {
    expect(formatContextLength(1_000_000)).toBe("1M");
    expect(formatContextLength(10_000_000)).toBe("10M");
  });

  it("formats fractional millions with one decimal", () => {
    expect(formatContextLength(1_500_000)).toBe("1.5M");
    expect(formatContextLength(1_048_576)).toBe("1.0M");
  });
});

describe("listCapabilityBadges", () => {
  const base: Pick<Model, "capabilities" | "context_length"> = {};

  it("returns nothing when no context and no capabilities", () => {
    expect(listCapabilityBadges({ ...base })).toEqual([]);
  });

  it("puts the context badge last (rightmost)", () => {
    const badges = listCapabilityBadges({
      capabilities: { vision: true },
      context_length: 128000,
    });
    expect(badges[badges.length - 1]).toEqual({ key: "context", label: "128K" });
  });

  it("lists capabilities in the canonical label order", () => {
    const badges = listCapabilityBadges({
      capabilities: {
        function_calling: true,
        vision: true,
        reranker: true,
        audio_speech: true,
      },
    });
    expect(badges.map((b) => b.key)).toEqual([
      "vision",
      "audio_speech",
      "function_calling",
      "reranker",
    ]);
  });

  it("uses the full Details-tab labels", () => {
    const badges = listCapabilityBadges({
      capabilities: { function_calling: true, image_generation: true },
    });
    expect(badges).toContainEqual({ key: "function_calling", label: "Function Calling" });
    expect(badges).toContainEqual({ key: "image_generation", label: "Image Gen" });
  });

  it("ignores falsey capabilities", () => {
    const badges = listCapabilityBadges({
      capabilities: { vision: false, function_calling: true },
    });
    expect(badges.map((b) => b.key)).toEqual(["function_calling"]);
  });

  it("surfaces all reported capabilities, not a curated subset", () => {
    const badges = listCapabilityBadges({
      capabilities: { reranker: true, audio_speech: true, image_to_image: true },
    });
    expect(badges.map((b) => b.key)).toEqual(["audio_speech", "image_to_image", "reranker"]);
  });

  it("omits the context badge when context_length is missing or zero", () => {
    expect(listCapabilityBadges({ capabilities: { vision: true } })).toEqual([
      { key: "vision", label: "Vision" },
    ]);
    expect(
      listCapabilityBadges({ context_length: 0, capabilities: { vision: true } }).map((b) => b.key),
    ).toEqual(["vision"]);
  });

  it("keeps the canonical labels map covering all known keys", () => {
    for (const key of [
      "vision",
      "audio_transcriptions",
      "audio_speech",
      "image_generation",
      "image_to_image",
      "function_calling",
      "reranker",
    ]) {
      expect(capabilityLabels[key]).toBeTruthy();
    }
  });

  it("gives every surfaced badge key a pastel color class", () => {
    const badges = listCapabilityBadges({
      context_length: 128000,
      capabilities: {
        vision: true,
        audio_transcriptions: true,
        audio_speech: true,
        image_generation: true,
        image_to_image: true,
        function_calling: true,
        reranker: true,
      },
    });
    // 7 capabilities + context
    expect(badges.length).toBe(8);
    for (const badge of badges) {
      expect(capabilityBadgeClass[badge.key], `missing color for ${badge.key}`).toBeTruthy();
    }
  });
});

describe("resolveCapabilitySource", () => {
  it("returns undefined when nothing is known", () => {
    expect(resolveCapabilitySource({ capabilities: { vision: true } }, "vision")).toBeUndefined();
  });

  it("falls back to the caller-supplied default", () => {
    expect(
      resolveCapabilitySource({ capabilities: { vision: true } }, "vision", "discovered"),
    ).toBe("discovered");
  });

  it("prefers an explicit per-model override over the default", () => {
    const model: Pick<Model, "capabilities" | "context_length" | "capabilitySources"> = {
      capabilities: { vision: true, function_calling: true },
      capabilitySources: { vision: "configured" },
    };
    expect(resolveCapabilitySource(model, "vision", "discovered")).toBe("configured");
    expect(resolveCapabilitySource(model, "function_calling", "discovered")).toBe("discovered");
  });
});

describe("listCapabilityBadges source", () => {
  it("leaves source undefined without a default (neutral style)", () => {
    const badges = listCapabilityBadges({ capabilities: { vision: true } });
    expect(badges[0].source).toBeUndefined();
  });

  it("stamps the default source onto every badge including context", () => {
    const badges = listCapabilityBadges(
      { capabilities: { vision: true }, context_length: 32768 },
      { defaultSource: "discovered" },
    );
    expect(badges.map((b) => b.source)).toEqual(["discovered", "discovered"]);
  });

  it("lets explicit overrides win per badge", () => {
    const badges = listCapabilityBadges(
      {
        capabilities: { vision: true, function_calling: true },
        capabilitySources: { function_calling: "configured" },
      },
      { defaultSource: "discovered" },
    );
    expect(badges.find((b) => b.key === "vision")?.source).toBe("discovered");
    expect(badges.find((b) => b.key === "function_calling")?.source).toBe("configured");
  });
});

describe("capability source presentation", () => {
  it("has tooltip text for every source", () => {
    for (const source of ["discovered", "configured", "unknown"] as const) {
      expect(capabilitySourceLabels[source]).toBeTruthy();
    }
  });

  it("gives discovered badges a dashed outline class and configured none", () => {
    expect(capabilitySourceBadgeClass.discovered).toContain("border-dashed");
    expect(capabilitySourceBadgeClass.configured).toBe("");
  });
});
