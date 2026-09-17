#!/usr/bin/env bun

import { $ } from "bun";
import { writeFile } from "node:fs/promises";
import { HOME, REPORT } from "./fleet_config.ts";
import { profileModel } from "./fleet_test.ts";

// fleet_universal_maximal.ts — parses EVERYTHING from ik_llama.cpp, works for ANY model
// Architecture-aware flag selection, exact log format matching, source-derived formulas
// Includes: SSM state size calculation, MLA kv_lora_rank parsing, recurrent layer detection

const models = (await $`find ${HOME}/models -name "*.gguf" -type f`.text())
  .trim()
  .split("\n")
  .filter(Boolean)
  .slice(0, 5);

const results = [];

console.log(`Found ${models.length} models to profile\n`);

for (const model of models) {
  try {
    const result = await profileModel(model);
    if (result) results.push(result);
  } catch (e) {
    console.error(`Failed to profile ${model}:`, e);
  }
}

results.sort((a, b) => b.context.actual_max - a.context.actual_max);

console.log("\n" + "=".repeat(80));

console.log("FINAL RESULTS");

console.log("=".repeat(80));

results.forEach((r) => {
  const arch = r.architecture.is_hybrid
    ? "HYBRID"
    : r.architecture.is_mla
      ? "MLA"
      : r.architecture.is_moe
        ? "MoE"
        : r.architecture.is_recurrent
          ? "SSM"
          : "standard";
  console.log(
    `${r.context.actual_max.toString().padStart(8)} | ${r.model.padEnd(40)} | ${r.architecture.detected?.padEnd(12)} | ${arch}`,
  );
});

await writeFile(REPORT, JSON.stringify(results, null, 2));

console.log(`\nFull report saved to: ${REPORT}`);
