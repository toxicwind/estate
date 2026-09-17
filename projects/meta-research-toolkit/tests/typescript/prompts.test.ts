import { describe, it, expect } from "bun:test";
import { PromptOrchestrator } from "../../src/typescript/prompts/orchestrator";
import { MetaClient, ChatRequestSchema } from "../../src/typescript/api/meta-client";

describe("PromptOrchestrator", () => {
  const orch = new PromptOrchestrator();

  it("lists 5 strategies", () => {
    const s = orch.listStrategies();
    expect(s.length).toBe(5);
  });

  it("retrieves citation_activation", () => {
    const s = orch.getStrategy("citation_activation");
    expect(s).not.toBeUndefined();
    expect(s!.strategy).toBe("citation");
    expect(s!.citations).toContain("arXiv:2608.29109");
  });

  it("renders a prompt pair", () => {
    const p = orch.renderPrompt("self_report_audit");
    expect(p).not.toBeNull();
    expect(p!.system).toContain("Muse Spark");
    expect(p!.user).toContain("47.7%");
  });
});

describe("MetaClient", () => {
  it("constructs with defaults", () => {
    const c = new MetaClient();
    expect(c).toBeDefined();
  });

  it("validates chat requests", () => {
    const valid = {
      model: "muse-spark",
      messages: [{ role: "user" as const, content: "hello" }],
    };
    expect(() => ChatRequestSchema.parse(valid)).not.toThrow();
  });
});
