#!/usr/bin/env bun
/**
 * Recursive Integration — sovereign, sovereign-projects, projects
 * Cuts across all three folders with concrete actions
 */

import { $ } from "bun";

const ROOT = "/home/toxic";
const SOVEREIGN = `${ROOT}/sovereign`;
const SOV_PROJECTS = `${ROOT}/projects/sovereign-projects`;
const PROJECTS = `${ROOT}/projects`;

async function run() {
  console.log("=== RECURSIVE INTEGRATION START ===");

  // 1. Sovereign: ensure helpers are executable
  console.log("1. Sovereign helpers executable...");
  await $`chmod +x ${SOVEREIGN}/helpers/*.ts ${SOVEREIGN}/helpers/*.sh 2>/dev/null || true`;

  // 2. Sovereign-projects: audit contents
  console.log("2. Sovereign-projects audit...");
  const spContents = await $`ls -1 ${SOV_PROJECTS}`.text();
  console.log(`   Contents: ${spContents.trim().replace(/\n/g, ", ")}`);

  // 3. Projects: filter relevant (non-WII, non-BurpSuite)
  console.log("3. Projects filtering (WII excluded, BurpSuite excluded)...");
  const allProjects = (await $`ls -1 ${PROJECTS}`.text())
    .split("\n")
    .filter(Boolean);
  const relevant = allProjects.filter(
    (p) =>
      !p.toLowerCase().includes("wii") &&
      !p.toLowerCase().includes("burp") &&
      !p.toLowerCase().includes("cosmic") &&
      p !== "projects/.ignore",
  );
  console.log(`   Total: ${allProjects.length}, Relevant: ${relevant.length}`);

  // 4. Wire cross-folder: create integration marker
  console.log("4. Creating cross-folder integration markers...");
  const marker = {
    timestamp: new Date().toISOString(),
    sovereign: {
      path: SOVEREIGN,
      helpers: [
        "git-mutator",
        "ast-migrate",
        "health-audit",
        "mesh-probe",
        "safe-rg-audit",
        "hardware-telemetry",
        "clean-orphans",
      ],
    },
    sovereignProjects: {
      path: SOV_PROJECTS,
      subdirs: spContents.trim().split("\n").filter(Boolean),
    },
    projects: {
      path: PROJECTS,
      total: allProjects.length,
      relevant: relevant.length,
      samples: relevant.slice(0, 10),
    },
  };

  await Bun.write(
    `${ROOT}/.recursive-integration.json`,
    JSON.stringify(marker, null, 2),
  );
  console.log(`   Marker written to ${ROOT}/.recursive-integration.json`);

  // 5. Git commit the integration
  console.log("5. Committing recursive integration...");
  await $`cd ${ROOT} && git add .recursive-integration.json && git commit -m "recursive integration: sovereign + sovereign-projects + projects cross-wired with concrete markers" 2>&1`;

  console.log("=== RECURSIVE INTEGRATION COMPLETE ===");
}

run().catch(console.error);
