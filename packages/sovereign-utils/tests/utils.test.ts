import { describe, it, expect } from "bun:test";
import { setManifest, resolveCapability, getAllCapabilities, getSynthesisHint } from "../src/capabilities/index";
import { evaluatePolicy } from "../src/policy/index";
import type { CapabilityManifest } from "../src/capabilities/manifest";
import type { Policy } from "../src/policy/types";

describe("@sovereign/utils", () => {
  describe("capabilities", () => {
    const testManifest: CapabilityManifest = {
      schemaVersion: "1.0",
      generatedAt: new Date().toISOString(),
      entries: [
        {
          name: "@oh-my-pi/pi-coding-agent#keyText",
          kind: "export",
          provider: "src/extensibility/shim.ts",
          aliases: ["@mariozechner/pi-coding-agent#keyText"],
          synthesize: "export function keyText() { return ''; }",
        },
      ],
    };

    it("resolves primary capability name", () => {
      setManifest(testManifest);
      expect(resolveCapability("@oh-my-pi/pi-coding-agent#keyText")).toBe("src/extensibility/shim.ts");
    });

    it("resolves alias", () => {
      setManifest(testManifest);
      expect(resolveCapability("@mariozechner/pi-coding-agent#keyText")).toBe("src/extensibility/shim.ts");
    });

    it("returns null for unknown capability", () => {
      setManifest(testManifest);
      expect(resolveCapability("@unknown/capability")).toBeNull();
    });

    it("returns synthesis hint", () => {
      setManifest(testManifest);
      expect(getSynthesisHint("@oh-my-pi/pi-coding-agent#keyText")).toContain("keyText");
    });

    it("returns all capabilities", () => {
      setManifest(testManifest);
      expect(getAllCapabilities().length).toBe(1);
    });
  });

  describe("policy channel", () => {
    const testPolicy: Policy = {
      schemaVersion: "1.0",
      mode: "deny",
      inheritFromParent: true,
      tools: {
        read: { kind: "allow" },
        destructive_tool: { kind: "deny", reason: "strictly blocked" },
      },
      rules: [
        {
          match: { tool: "bash", command: "rm -rf /" },
          decision: { kind: "deny", reason: "catastrophic command" },
        },
        {
          match: { tool: "bash" },
          decision: { kind: "escalate", to: "parent", prompt: "Approve bash" },
        },
      ],
    };

    it("respects tool override allow", () => {
      expect(evaluatePolicy(testPolicy, "read")).toEqual({ kind: "allow" });
    });

    it("respects tool override deny", () => {
      expect(evaluatePolicy(testPolicy, "destructive_tool")).toEqual({
        kind: "deny",
        reason: "strictly blocked",
      });
    });

    it("matches specific command rule before general rule", () => {
      expect(evaluatePolicy(testPolicy, "bash", "rm -rf /")).toEqual({
        kind: "deny",
        reason: "catastrophic command",
      });
    });

    it("falls back to default mode when no tool or rule matches", () => {
      expect(evaluatePolicy(testPolicy, "unspecified_tool")).toEqual({
        kind: "deny",
        reason: "default deny by policy mode",
      });
    });
  });
});
