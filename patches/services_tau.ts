// ============================================================================
// Live Hotfix: services.tau
// Author: sovereign
// Reason: Clean .tau cutover from obsolete .pi environment paths
// ============================================================================

import type { ServiceDef } from "../src/types/index.ts";

export const TARGET = "services.tau";
export const VERSION = "1.1.0";
export const AUTHOR = "sovereign";
export const REASON = "Permanent .tau path resolution without monkey patching";
export const ENABLED = true;

export const impl: ServiceDef = {
  id: "tau",
  name: "tau",
  portKey: "PI_AGENT_PORT",
  run: "exec /home/toxic/sovereign/agent",
  dir: "/home/toxic",
  readyCmd: "sleep 1 && echo ready",
  group: "agents",
  autoStart: true,
  mise: true,
  env: {
    PI_CONFIG_DIR: "/home/toxic/.tau",
    PI_AGENT_DIR: "/home/toxic/.tau/agent",
    PI_CODING_AGENT: "true",
    PI_REASONING_LEVEL: "high",
    PI_SUBAGENT_MODEL: "thinkingmachines/inkling",
  },
};
