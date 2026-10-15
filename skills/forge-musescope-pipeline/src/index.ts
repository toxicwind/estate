#!/usr/bin/env bun
/**
 * Main entry point for the musescope JSON → parquet → analysis pipeline.
 * Modular design with tampermonkey-style config.
 */

import { config } from "./config.js";
import { parseMusescopeJson } from "./stages/parse.js";
import { convertToParquet } from "./stages/convert.js";
import { runAnalysis } from "./stages/analyze.js";
import { runFerretDenRecon } from "./stages/ferret.js";

async function main() {
  // Load config
  const cfg = config.getAll();
  
  console.log("🚀 Starting musescope pipeline");
  console.log(`📁 Input: ${cfg.inputPath}`);
  console.log(`📁 Output: ${cfg.outputDir}`);
  
  try {
    // Stage 1: Parse JSON
    const parsed = await parseMusescopeJson(cfg);
    
    // Stage 2: Convert to parquet
    const parquetFiles = await convertToParquet(parsed, cfg);
    
    // Stage 3: Analysis (optional)
    if (cfg.runAnalysis) {
      await runAnalysis(parquetFiles, cfg);
    }
    
    // Stage 4: Ferret-den integration (optional)
    if (cfg.runFerretDen) {
      await runFerretDenRecon(parquetFiles, cfg);
    }
    
    console.log("✅ Pipeline completed successfully");
  } catch (err) {
    console.error("❌ Pipeline failed:", err);
    process.exit(1);
  }
}

// Run if executed directly
if (import.meta.main) {
  main();
}

export default main;