#!/usr/bin/env bun
/**
 * Sovereign-Projects Integration with Sovereign Workspace
 * Concrete links from sovereign-projects subdirs to sovereign helpers
 */

import { $ } from "bun";

const SOV_PROJECTS = "/home/toxic/projects/sovereign-projects";
const SOVEREIGN = "/home/toxic/sovereign";

async function integrate() {
  console.log("=== SOVEREIGN-PROJECTS -> SOVEREIGN INTEGRATION ===");
  
  // 1. Link herd engines to sovereign health-audit ports
  const herdPorts = {
    "herd": 25100,
    "llama-swap": 25100,
    "mesh": 25127,
    "yote": 25102
  };
  
  // 2. Create shared config reference
  const config = {
    timestamp: new Date().toISOString(),
    sovereignProjectsPath: SOV_PROJECTS,
    symlinkFrom: "/home/toxic/sovereign-projects",
    linkedToSovereign: {
      healthAudit: `${SOVEREIGN}/helpers/health-audit.ts`,
      gitMutator: `${SOVEREIGN}/helpers/git-mutator/cli.ts`,
      portsEnv: `${SOVEREIGN}/config/ports.env`
    },
    subdirIntegrations: {
      "herd": { path: `${SOV_PROJECTS}/herd`, sovereignPort: "herd=25100", engines: true },
      "zedra": { path: `${SOV_PROJECTS}/zedra`, sovereignLink: "zed integration via sovereign-zed" },
      "boundless": { path: `${SOV_PROJECTS}/boundless`, sovereignLink: "openfang/yote services" },
      "extensions": { path: `${SOV_PROJECTS}/extensions`, sovereignLink: "semantouch/engram" },
      "tau": { path: `${SOV_PROJECTS}/tau`, sovereignLink: "tau packages/coding-agent" },
      "sovereign-internal": { path: `${SOV_PROJECTS}/sovereign-internal`, sovereignLink: "AGENTS.md mirror" }
    }
  };
  
  await Bun.write(`${SOV_PROJECTS}/.sovereign-integration.json`, JSON.stringify(config, null, 2));
  console.log(`Written: ${SOV_PROJECTS}/.sovereign-integration.json`);
  
  // 3. Symlink sovereign helpers into sovereign-projects for direct access
  await $`ln -sf ${SOVEREIGN}/helpers ${SOV_PROJECTS}/.sovereign-helpers 2>/dev/null || true`;
  console.log("Symlinked sovereign helpers into sovereign-projects/.sovereign-helpers");
  
  // 4. Git commit
  await $`cd /home/toxic && git add projects/sovereign-projects/.sovereign-integration.json projects/sovereign-projects/.sovereign-helpers 2>/dev/null && git commit -m "sovereign-projects integration: linked herd/zedra/boundless/extensions/tau to sovereign workspace helpers (health-audit, git-mutator, ports.env)" 2>&1`;
}

integrate().catch(console.error);
