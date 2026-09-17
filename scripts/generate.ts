// ============================================================================
// RETIRED 2026-09-14 — DO NOT RUN.
// pitchfork.toml and mise.toml are now the source of truth, edited directly.
// Running this generator OVERWRITES pitchfork.toml and DESTROYS native additions
// (coyote env, free-zed-gateway, tau path fix, dnsmasq, hand-tuned readiness).
// Audit 2026-09-14: generator defines 36 services, pitchfork has 28 daemons.
// 11 generator-only services are superseded (llama.cpp forks -> herd), dev-only,
// or not running. 3 pitchfork daemons (dnsmasq, free-zed-gateway, tau-code) were
// added natively post-generator. Generator sources kept for reference only.
// Open: fate of antigravity-cli, pi-agent, pi-web-dashboard, qed, zedra-host
// (defined in generator, not in pitchfork, not observed running).
// ============================================================================
// ============================================================================
// SOVEREIGN — Config Generation CLI Entry Point
// Run: bun run scripts/generate.ts
// ============================================================================

import { resolve } from "node:path";
import { generateAll } from "../src/generators/index.ts";

const root = process.env.SOVEREIGN_ROOT || resolve(import.meta.dir, "..");
await generateAll(root);
