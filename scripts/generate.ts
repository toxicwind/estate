// ============================================================================
// SOVEREIGN — Config Generation CLI Entry Point
// Run: bun run scripts/generate.ts
// ============================================================================

import { resolve } from "path";
import { generateAll } from "../src/generators/index.ts";

const root = process.env.SOVEREIGN_ROOT || resolve(import.meta.dir, "..");
await generateAll(root);