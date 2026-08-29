// ============================================================================
// SOVEREIGN — Project Fork Services (/home/toxic/projects/)
// First-class forks with their own build toolchains
// ============================================================================

import type { ServiceDef } from "../types/index.ts";

export const FORK_SERVICES: ServiceDef[] = [
  // ── AGENT RUNTIMES ──
  {
    id: "pi-agent",
    name: "pi-agent",
    portKey: "PI_AGENT_PORT",
    run: "exec /home/toxic/.bun/bin/bun run /home/toxic/projects/pi-agent/packages/coding-agent/src/cli.ts --session-dir /home/toxic/.pi/agent/sessions",
    dir: "/home/toxic",
    readyCmd: "sleep 3 && echo ready",
    group: "core",
    autoStart: true,
    mise: true,
    env: {
      PI_CONFIG_PATH: "/home/toxic/.pi/agent/config.yaml",
      PI_AGENT_DIR: "/home/toxic/.pi/agent",
      PI_CODING_AGENT: "true",
      PI_REASONING_LEVEL: "high",
    },
  },
  {
    id: "kimi-code",
    name: "kimi-code-sovereign",
    portKey: "KIMI_CODE_PORT",
    run: "exec /home/toxic/projects/kimi-code-sovereign/apps/kimi-code/dist/main.mjs web --no-open --port 25126",
    dir: "/home/toxic/projects/kimi-code-sovereign",
    readyHttp: "/health",
    group: "main",
    autoStart: true,
    mise: true,
    env: { KIMI_CODE_PORT: "25126" },
  },

  // ── GATEWAYS / PROXIES ──
  {
    id: "antigravity-gateway",
    name: "antigravity-gateway",
    portKey: "ANTIGRAVITY_GATEWAY_PORT",
    run: "exec bun --hot run server.ts",
    dir: "/home/toxic/projects/antigravity-gateway-master",
    readyHttp: "/health",
    group: "main",
    autoStart: true,
    mise: true,
    env: { PORT: "25128" },
  },

  // ── REMOTE AGENT HOSTS ──
  {
    id: "zedra-host",
    name: "zedra-host",
    portKey: "ZEDRA_HOST_PORT",
    run: "exec cargo run -p zedra-host --release",
    dir: "/home/toxic/projects/zedra-tanlethanh",
    readyHttp: "/health",
    group: "main",
    autoStart: true,
    mise: false,
    env: { PORT: "25130" },
  },

  // ── IDE SERVICES ──
  {
    id: "antigravity-cli",
    name: "antigravity-cli",
    portKey: "ANTIGRAVITY_CLI_PORT",
    run: "exec bun run src/main.ts",
    dir: "/home/toxic/projects/antigravity-ide-cli",
    readyHttp: "/health",
    group: "main",
    autoStart: true,
    mise: false,
    env: { PORT: "25140" },
  },
];