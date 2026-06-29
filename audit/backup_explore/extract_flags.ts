#!/usr/bin/env bun
/**
 * extract_flags.ts – Pulls flags directly from the binary.
 * Added .nothrow() to ignore exit code 1 and improved regex robustness.
 */

import { $ } from "bun";

const BIN = process.argv[2] || "/home/toxic/llama-cpp-turboquant/build/bin/llama-server";

interface FlagInfo {
  flags: string[];
  description: string;
}

async function getFlags(): Promise<FlagInfo[]> {
  const output = (await $`${BIN} --help`.quiet().nothrow()).text();
  const lines = output.split("\n");
  const flags: FlagInfo[] = [];

  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith("-") && trimmed.includes("  ")) {
      // Split into flags part and description part using at least 2 spaces
      const parts = trimmed.split(/\s{2,}/);
      if (parts.length >= 2) {
        let flagPart = parts[0];
        let descPart = parts.slice(1).join(" ");
        
        // Remove trailing arguments like N or FNAME
        flagPart = flagPart.replace(/\s+[A-Z0-9_]+$/, "");
        
        const flagList = flagPart.split(",").map(s => s.trim()).filter(s => s.length > 0);
        flags.push({
          flags: flagList,
          description: descPart,
        });
      }
    }
  }
  return flags;
}

const flags = await getFlags();
console.log(JSON.stringify(flags, null, 2));
