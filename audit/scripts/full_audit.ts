// Full Audit - orchestrates all audit checks
// Run: bun run audit/scripts/full_audit.ts

import { spawn } from "node:child_process";

const SCRIPTS_DIR = import.meta.dir;

interface AuditStep {
  name: string;
  script: string;
  critical: boolean;
}

const STEPS: AuditStep[] = [
  { name: "AGENTS.md Inventory", script: "inventory_agents_md.ts", critical: true },
  { name: "Service Health Check", script: "audit_services.ts", critical: true },
  { name: "Profile Validation", script: "profile_manager.ts", critical: false },
];

async function runScript(script: string): Promise<{ code: number; output: string }> {
  return new Promise((resolve) => {
    const proc = spawn("bun", ["run", `${SCRIPTS_DIR}/${script}`], {
      stdio: ["ignore", "pipe", "pipe"],
    });
    let output = "";
    proc.stdout.on("data", (d) => (output += d.toString()));
    proc.stderr.on("data", (d) => (output += d.toString()));
    proc.on("close", (code) => resolve({ code: code ?? 1, output }));
  });
}

async function main() {
  console.log("=== SOVEREIGN FULL AUDIT ===\n");
  let failed = 0;

  for (const step of STEPS) {
    console.log(`\n▶ Running: ${step.name}...`);
    const { code, output } = await runScript(step.script);
    console.log(output);
    if (code !== 0) {
      console.error(`  ❌ FAILED (exit ${code})`);
      if (step.critical) failed++;
    } else {
      console.log(`  ✅ PASS`);
    }
  }

  console.log(`\n=== AUDIT COMPLETE: ${failed} critical failures ===`);
  process.exit(failed > 0 ? 1 : 0);
}

main();
