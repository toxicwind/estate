// ============================================================================
// SOVEREIGN — Generator Index
// ============================================================================

import type { Generator, TemplateContext } from "../types/index.ts";
import { ALL_SERVICES } from "../services/index.ts";
import { parsePortsEnv } from "../utils/ports.ts";
import { pitchforkGenerator } from "./pitchfork.ts";
import { miseGenerator } from "./mise.ts";

const GENERATORS: Generator[] = [
  pitchforkGenerator,
  miseGenerator,
];

export async function generateAll(root: string = process.cwd()): Promise<void> {
  console.log("🔧 Generating sovereign configs from ports.env + service definitions...");

  // Build context
  const ports = parsePortsEnv(root);
  const portsRecord: Record<string, number> = {};
  for (const [k, v] of ports) portsRecord[k] = v;

  // Validate all required ports exist
  const requiredKeys = ALL_SERVICES.map(s => s.portKey);
  const missing = requiredKeys.filter(k => !ports.has(k));
  if (missing.length > 0) {
    console.error("❌ Missing port keys:", missing.join(", "));
    process.exit(1);
  }

  const ctx: TemplateContext = {
    ports: portsRecord,
    services: ALL_SERVICES,
    groups: { core: ALL_SERVICES.map(s => s.id) },
    timestamp: new Date().toISOString(),
    sovRoot: root,
  };

  // Run all generators
  for (const gen of GENERATORS) {
    const output = gen.generate(ctx);
    const outputPath = join(root, gen.outputPath);
    await Bun.write(outputPath, output);
    console.log(`✅ ${gen.name} generated (${output.length} chars)`);
  }

  console.log("\n📊 Summary:");
  console.log(`  Services: ${ALL_SERVICES.length}`);
  console.log(`  Auto-start: ${ALL_SERVICES.filter(s => s.autoStart).length} always-on`);
  console.log(`  On-demand: ${ALL_SERVICES.filter(s => !s.autoStart).length} configured`);
  console.log(`  Ports loaded: ${ports.size}`);
  console.log(`  Generators: ${GENERATORS.length}`);
}

import { join } from "path";