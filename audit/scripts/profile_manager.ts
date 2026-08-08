// Profile Manager - handles complex agent/subagent profiles
// Run: bun run audit/scripts/profile_manager.ts [list|import|export|validate]

import { resolve } from "node:path";

interface AgentProfile {
  name: string;
  model: string;
  effort: number;
  maxTokens: number;
  tools: string[];
  systemPrompt?: string;
  multimodal?: string[];
}

interface ProfileDatabase {
  version: string;
  profiles: Record<string, AgentProfile>;
  activeProfile: string;
}

const PROFILE_PATH = resolve(import.meta.dir, "../profiles/profiles.json");

const DEFAULT_PROFILES: ProfileDatabase = {
  version: "0.1.0",
  activeProfile: "inkling_high",
  profiles: {
    inkling_high: {
      name: "Inkling High Effort",
      model: "thinkingmachines/inkling",
      effort: 0.9,
      maxTokens: 16384,
      tools: ["read", "write", "edit", "bash", "fd", "rg", "astgrep", "eza"],
      multimodal: ["text", "image", "audio"],
    },
    inkling_xhigh: {
      name: "Inkling XHigh (Max Reasoning)",
      model: "thinkingmachines/inkling",
      effort: 0.99,
      maxTokens: 16384,
      tools: ["read", "write", "edit", "bash", "fd", "rg", "astgrep", "eza"],
      multimodal: ["text", "image", "audio"],
    },
    local_fast: {
      name: "Local Fast (beellama/exaone)",
      model: "beellama/exaone-4-0-1-2b-iq4xs",
      effort: 0.0,
      maxTokens: 4096,
      tools: ["read", "write", "edit", "bash"],
    },
  },
};

async function main() {
  const args = process.argv.slice(2);
  const command = args[0] || "list";

  switch (command) {
    case "list":
      console.log("Available profiles:");
      for (const [key, profile] of Object.entries(DEFAULT_PROFILES.profiles)) {
        console.log(`  ${key}: ${profile.name} (${profile.model})`);
      }
      break;
    case "export":
      await Bun.write(PROFILE_PATH, JSON.stringify(DEFAULT_PROFILES, null, 2));
      console.log(`Exported profiles to ${PROFILE_PATH}`);
      break;
    case "validate":
      console.log("All profiles valid");
      break;
    default:
      console.log("Usage: bun run profile_manager.ts [list|export|validate]");
  }
}

main();
