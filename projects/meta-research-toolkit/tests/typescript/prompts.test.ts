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

  it("returns a defensive copy from listStrategies", () => {
    const s = orch.listStrategies();
    s[0].name = "tampered";
    s[0].citations.push("bogus");
    expect(orch.getStrategy("citation_activation")).toBeDefined();
    expect(orch.listStrategies()[0].citations).not.toContain("bogus");
  });

  it("exposes strategy names and kind lookup", () => {
    expect(orch.strategyNames()).toEqual([
      "citation_activation",
      "self_report_audit",
      "mechanistic_steering",
      "trilemma_argument",
      "rule_of_two_framework",
    ]);
    const byKind = orch.getByStrategy("mechanistic");
    expect(byKind.length).toBe(1);
    expect(byKind[0].name).toBe("mechanistic_steering");
  });

  it("renderPrompt returns null for unknown names", () => {
    expect(orch.renderPrompt("no_such_strategy")).toBeNull();
  });

  it("renderMessages produces a chat-ready system+user pair", () => {
    const messages = orch.renderMessages("trilemma_argument");
    expect(messages.length).toBe(2);
    expect(messages[0].role).toBe("system");
    expect(messages[1].role).toBe("user");
    // Validates against the same schema MetaClient.chat enforces.
    expect(() =>
      ChatRequestSchema.parse({ model: "m", messages })
    ).not.toThrow();
  });

  it("renderMessages throws on unknown names", () => {
    expect(() => orch.renderMessages("no_such_strategy")).toThrow(
      /unknown strategy/
    );
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

  it("rejects invalid chat requests", () => {
    expect(() =>
      ChatRequestSchema.parse({ model: "", messages: [] })
    ).toThrow();
    expect(() =>
      ChatRequestSchema.parse({
        model: "m",
        messages: [{ role: "user", content: "hi" }],
        temperature: 5,
      })
    ).toThrow();
  });

  it("reports apiKey presence without exposing it", () => {
    const withKey = new MetaClient({ apiKey: "not-a-real-key" });
    const withoutKey = new MetaClient({ apiKey: "" });
    expect(withKey.hasApiKey).toBe(true);
    expect(withoutKey.hasApiKey).toBe(false);
  });

  it("chat refuses to send without an API key", async () => {
    const c = new MetaClient({ apiKey: "" });
    await expect(
      c.chat({ model: "m", messages: [{ role: "user", content: "hi" }] })
    ).rejects.toThrow(/no API key/i);
  });
});
