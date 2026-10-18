import { describe, expect, test } from "bun:test";
import { readFileSync, existsSync } from "node:fs";

describe("OpenFang / Rig Gemini EAP Completions & Oracle Agent Pipeline", () => {
  test("OpenFang canonical config (openfang-25196.toml) points default_model to cuttinggate (:25200) -> hodos", () => {
    const configPath = "/home/toxic/estate/config/openfang-25196.toml";
    expect(existsSync(configPath)).toBe(true);
    const content = readFileSync(configPath, "utf8");
    expect(content).toContain('model = "google/gemini-3.8-flash"');
    expect(content).toContain('base_url = "http://127.0.0.1:25200/v1"');
    expect(content).toContain('api_key_env = "HODOS_API_KEY"');
    expect(content).not.toContain("25100");
  });

  test("Oracle agent manifest exists in ranch/rig/agents and estate/agents with first-class EAP completion wiring", () => {
    const ranchOracle = "/home/toxic/estate/ranch/rig/agents/oracle.toml";
    const estateOracle = "/home/toxic/estate/agents/oracle/agent.toml";
    expect(existsSync(ranchOracle)).toBe(true);
    expect(existsSync(estateOracle)).toBe(true);

    const ranchContent = readFileSync(ranchOracle, "utf8");
    expect(ranchContent).toContain('name = "oracle"');
    expect(ranchContent).toContain('model = "google/gemini-3.8-flash"');
    expect(ranchContent).toContain('base_url = "http://127.0.0.1:25200/v1"');
    expect(ranchContent).toContain('"tool_search"');
    expect(ranchContent).toContain('"market_settle"');
  });

  test("All estate agent manifests are cleansed of obsolete :25100 and point to cuttinggate (:25200) -> hodos", () => {
    const manifests = [
      "/home/toxic/estate/agents/coyote/agent.toml",
      "/home/toxic/estate/agents/assistant/agent.toml",
      "/home/toxic/estate/agents/oracle-market/agent.toml",
      "/home/toxic/estate/agents/trailboss/agent.toml",
    ];

    for (const p of manifests) {
      const c = readFileSync(p, "utf8");
      expect(c).toContain('base_url = "http://127.0.0.1:25200/v1"');
      expect(c).toContain('model = "google/gemini-3.8-flash"');
      expect(c).not.toContain('base_url = "http://127.0.0.1:25100/v1"');
    }
  });

  test("Confidential Gemini Tool Retrieval EAP doc is strictly gitignored in estate-recon", () => {
    const eapDoc = "/home/toxic/estate/estate-recon/gemini-3.8-flash-tool-retrieval-eap.md";
    expect(existsSync(eapDoc)).toBe(true);
    const gitignore = readFileSync("/home/toxic/estate/.gitignore", "utf8");
    expect(gitignore).toContain("estate-recon");
  });
});
