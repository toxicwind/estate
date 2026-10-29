#!/usr/bin/env bun
/**
 * Estate-Projects Integration with Estate Workspace
 * Concrete links from estate-projects subdirs to estate helpers
 */

import { $ } from "bun";

const SOV_PROJECTS = "/home/toxic/projects/estate-projects";
const ESTATE = "/home/toxic/pens/estate";

async function integrate() {
  console.log("=== ESTATE-PROJECTS -> ESTATE INTEGRATION ===");
  
  // 1. Link bornite engines to estate health-audit ports
  const herdPorts = {
    "bornite": 25100,
    "bornite": 25100,
    "mesh": 25127,
    "yote": 25102
  };
  
  // 2. Create shared config reference
  const config = {
    timestamp: new Date().toISOString(),
    estateProjectsPath: SOV_PROJECTS,
    symlinkFrom: "/home/toxic/pens/estate/products",
    linkedToEstate: {
      healthAudit: `${ESTATE}/helpers/health-audit.ts`,
      gitMutator: `${ESTATE}/helpers/git-mutator/cli.ts`,
      portsEnv: `${ESTATE}/config/ports.env`
    },
    subdirIntegrations: {
      "bornite": { path: `${SOV_PROJECTS}/bornite`, estatePort: "bornite=25100", engines: true },
      "zedra": { path: `${SOV_PROJECTS}/zedra`, estateLink: "zed integration via estate-zed" },
      "boundless": { path: `${SOV_PROJECTS}/boundless`, estateLink: "openfang/yote services" },
      "extensions": { path: `${SOV_PROJECTS}/extensions`, estateLink: "semantouch/engram" },
      "tau": { path: `${SOV_PROJECTS}/tau`, estateLink: "tau packages/coding-agent" },
      "estate-internal": { path: `${SOV_PROJECTS}/estate-internal`, estateLink: "AGENTS.md mirror" }
    }
  };
  
  await Bun.write(`${SOV_PROJECTS}/.estate-integration.json`, JSON.stringify(config, null, 2));
  console.log(`Written: ${SOV_PROJECTS}/.estate-integration.json`);
  
  // 3. Symlink estate helpers into estate-projects for direct access
  await $`ln -sf ${ESTATE}/helpers ${SOV_PROJECTS}/.estate-helpers 2>/dev/null || true`;
  console.log("Symlinked estate helpers into estate-projects/.estate-helpers");
  
  // 4. Git commit
  await $`cd /home/toxic && git add projects/estate-projects/.estate-integration.json projects/estate-projects/.estate-helpers 2>/dev/null && git commit -m "estate-projects integration: linked bornite/zedra/boundless/extensions/tau to estate workspace helpers (health-audit, git-mutator, ports.env)" 2>&1`;
}

integrate().catch(console.error);
